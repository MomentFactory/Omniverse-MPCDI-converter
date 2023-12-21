// Copyright 2023 NVIDIA CORPORATION
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "mpcdiFileFormat.h"
#include "tinyxml2.h"

#include <pxr/pxr.h>

#include <pxr/base/tf/diagnostic.h>
#include <pxr/base/tf/stringUtils.h>
#include <pxr/base/tf/token.h>

#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usd/usdaFileFormat.h>

#include <pxr/usd/usdGeom/mesh.h>
#include <pxr/usd/usdGeom/scope.h>
#include <pxr/usd/usdGeom/camera.h>
#include <pxr/usd/usdGeom/cube.h>
#include <pxr/usd/usdGeom/xformable.h>
#include <pxr/usd/usdGeom/xform.h>

#include <pxr/usd/usdLux/rectLight.h>

#include <pxr/base/gf/matrix3f.h>
#include <pxr/base/gf/vec3f.h>

#include <fstream>
#include <cmath>

PXR_NAMESPACE_OPEN_SCOPE

MpcdiFileFormat::MpcdiFileFormat() : SdfFileFormat(
										MpcdiFileFormatTokens->Id,
										MpcdiFileFormatTokens->Version,
										MpcdiFileFormatTokens->Target,
										MpcdiFileFormatTokens->Extension)
{
}

MpcdiFileFormat::~MpcdiFileFormat()
{
}

static const double defaultSideLengthValue = 1.0;


static double _ExtractSideLengthFromContext(const PcpDynamicFileFormatContext& context)
{
    // Default sideLength.
    double sideLength = defaultSideLengthValue;

    VtValue value;
    if (!context.ComposeValue(MpcdiFileFormatTokens->SideLength,
                              &value) ||
        value.IsEmpty()) {
        return sideLength;
    }

    if (!value.IsHolding<double>()) {
       
        return sideLength;
    }

    return value.UncheckedGet<double>();
}

static double
_ExtractSideLengthFromArgs(const SdfFileFormat::FileFormatArguments& args)
{
    // Default sideLength.
    double sideLength = defaultSideLengthValue;

    // Find "sideLength" file format argument.
    auto it = args.find(MpcdiFileFormatTokens->SideLength);
    if (it == args.end()) {
        return sideLength;
    }

    // Try to convert the string value to the actual output value type.
    double extractVal;
    bool success = true;
    extractVal = TfUnstringify<double>(it->second, &success);
    if (!success) {
        
        return sideLength;
    }

    sideLength = extractVal;
    return sideLength;
}

bool MpcdiFileFormat::CanRead(const std::string& filePath) const
{
	return true;
}

static float GetXMLFloat(tinyxml2::XMLElement* node, const std::string key)
{
	return std::stof(node->FirstChildElement(key.c_str())->GetText());
}

static std::string CleanNameForUSD(const std::string& name)
{
	std::string cleanedName = name;
	if(cleanedName.size() == 0)
	{
		return "Default";
	}

	if(cleanedName.size() == 1 && !TfIsValidIdentifier(cleanedName))
	{
		// If we have an index as a name, we only need to add _ beforehand.
		return CleanNameForUSD("_" + cleanedName);
	}

	return TfMakeValidIdentifier(cleanedName);
}

bool MpcdiFileFormat::Read(SdfLayer* layer, const std::string& resolvedPath, bool metadataOnly) const
{
	// these macros emit methods defined in the Pixar namespace
	// but not properly scoped, so we have to use the namespace
	// locally here - note this isn't strictly true since we had to open
	// the namespace scope anyway because the macros won't allow non-Pixar namespaces
	// to be used because of some auto-generated content

	// Read file, file exists?
	const std::ifstream filePath(resolvedPath);
	if(!filePath.good())
	{
		TF_CODING_ERROR("File doesn't exist with resolved path: " + resolvedPath);
		return false;
	}
	
	// Read XML file
	tinyxml2::XMLDocument doc;
	const tinyxml2::XMLError xmlReadSuccess = doc.LoadFile(resolvedPath.c_str());
	if(xmlReadSuccess != 0)
	{
		TF_CODING_ERROR("Failed to load xml file: " + resolvedPath);
		return false;
	}

	// Parsing of MPCDI data
	tinyxml2::XMLElement* rootNode = doc.RootElement();
	if(rootNode == nullptr)
	{
		TF_CODING_ERROR("XML Root node is null: " + resolvedPath);
		return false;
	}
	
	// Create a new anonymous layer and wrap a stage around it.
	SdfLayerRefPtr newLayer = SdfLayer::CreateAnonymous(".usd");
	UsdStageRefPtr stage = UsdStage::Open(newLayer);

	const auto& xformPath = SdfPath("/mpcdi_payload");
	auto mpdiScope = UsdGeomXform::Define(stage, xformPath);
	stage->SetDefaultPrim(mpdiScope.GetPrim());

	auto displayNode = rootNode->FirstChildElement("display");
	for(auto* buffer = displayNode->FirstChildElement("buffer"); buffer != nullptr; buffer = buffer->NextSiblingElement("buffer"))
	{
		const std::string bufferId = std::string(buffer->Attribute("id"));

		std::string bufferIdentifier = CleanNameForUSD(bufferId);

		SdfPath bufferPath = xformPath.AppendChild(TfToken(bufferIdentifier));
		auto bufferScope = UsdGeomScope::Define(stage, bufferPath);
		
		// Get region
		for(auto* regionNode = buffer->FirstChildElement("region"); regionNode != nullptr; regionNode = regionNode->NextSiblingElement("region"))
		{
			const std::string regionId = std::string(regionNode->Attribute("id"));
			const std::string cleanedRegionId = CleanNameForUSD(regionId);

			SdfPath regionPath = bufferPath.AppendChild(TfToken(cleanedRegionId));

			// Get Frustum
			auto frustumNode = regionNode->FirstChildElement("frustum");
			const auto frustumYaw = GetXMLFloat(frustumNode, "yaw") * -1.0f;
			const auto frustumPitch = GetXMLFloat(frustumNode, "pitch");
			const auto frustumRoll = GetXMLFloat(frustumNode, "roll");
			const auto frustumRightAngle = GetXMLFloat(frustumNode, "rightAngle");
			const auto frustumLeftAngle = GetXMLFloat(frustumNode, "leftAngle");
			const auto frustumUpAngle = GetXMLFloat(frustumNode, "upAngle");
			const auto frustumDownAngle = GetXMLFloat(frustumNode, "downAngle");

			constexpr const float toRad = 3.14159265358979323846 / 180.0;
			constexpr const float focalLength = 10.0f;
			constexpr const float focusDistance = 2000.0f;

			const float tanRight = std::tan(frustumRightAngle * toRad);
			const float tanLeft = std::tan(frustumLeftAngle * toRad);
			const float tanUp = std::tan(frustumUpAngle * toRad);
			const float tanDown = std::tan(frustumDownAngle * toRad);
			const float apertureH = (std::abs(tanRight) + std::abs(tanLeft)) * focalLength;
			const float apertureV = (std::abs(tanUp) + std::abs(tanDown)) * focalLength;
			const float lightWidth = std::abs(tanRight) + std::abs(tanLeft);
			const float lightHeight = std::abs(tanUp) + std::abs(tanDown);

			const float lensShiftH = (tanLeft + tanRight) / (tanLeft - tanRight);
			const float lensShiftV = (tanUp + tanDown) / (tanUp - tanDown);
			const float apertureOffsetH = lensShiftH * apertureH / 2.0;
			const float apertureOffsetV = lensShiftV * apertureV / 2.0;

			// Coordinate frame
			const float posScaling = 10.0f;
			auto coordFrameNode = regionNode->FirstChildElement("coordinateFrame");
			const auto posX = GetXMLFloat(coordFrameNode, "posx") * posScaling;
			const auto posY = GetXMLFloat(coordFrameNode, "posy") * posScaling;
			const auto posZ = GetXMLFloat(coordFrameNode, "posz") * posScaling;

			const auto yawX = GetXMLFloat(coordFrameNode, "yawx");
			const auto yawY = GetXMLFloat(coordFrameNode, "yawy");
			const auto yawZ = GetXMLFloat(coordFrameNode, "yawz");
			const auto pitchX = GetXMLFloat(coordFrameNode, "pitchx");
			const auto pitchY = GetXMLFloat(coordFrameNode, "pitchy");
			const auto pitchZ = GetXMLFloat(coordFrameNode, "pitchz");
			const auto rollX = GetXMLFloat(coordFrameNode, "rollx");
			const auto rollY = GetXMLFloat(coordFrameNode, "rolly");
			const auto rollZ = GetXMLFloat(coordFrameNode, "rollz");

			GfMatrix3f sourceToStandard = GfMatrix3f(pitchX, pitchY, pitchZ, yawX, yawY, yawZ, rollX, rollY, rollZ);
			auto newPosition = sourceToStandard * GfVec3f(posX, posY, posZ);
			newPosition[1] = -newPosition[1];
			newPosition[2] = -newPosition[2];

			// Camera
			UsdGeomCamera camera = UsdGeomCamera::Define(stage, regionPath);

			// Camera transform
			auto cameraXform = UsdGeomXformable(camera);
    		auto translateOperation = cameraXform.AddTranslateOp(UsdGeomXformOp::PrecisionFloat);
			translateOperation.Set<GfVec3f>(newPosition * 10.0);
			cameraXform.AddRotateYOp().Set(frustumYaw);
			cameraXform.AddRotateXOp().Set(frustumPitch);
			cameraXform.AddRotateZOp().Set(frustumRoll);

			// Set camera attributes
			camera.GetFocalLengthAttr().Set(focalLength);
			camera.GetFocusDistanceAttr().Set(focusDistance);
			camera.GetHorizontalApertureAttr().Set(apertureH);
			camera.GetHorizontalApertureOffsetAttr().Set(apertureOffsetH);
			camera.GetVerticalApertureAttr().Set(apertureV);
			camera.GetVerticalApertureOffsetAttr().Set(apertureOffsetV);

			// Light
			SdfPath lightPath = regionPath.AppendChild(TfToken("RectLight"));
			auto rectLight = UsdLuxRectLight::Define(stage, lightPath);
			auto lightXform = UsdGeomXformable(rectLight);
    		auto lightTranslateOperation = lightXform.AddTranslateOp(UsdGeomXformOp::PrecisionFloat);

			rectLight.GetPrim().CreateAttribute(
				TfToken("isProjector"), 
				SdfValueTypeNames->Bool
    		).Set(true);

			rectLight.GetPrim().CreateAttribute(
				TfToken("exposure"), 
				SdfValueTypeNames->Float
    		).Set(5.0f);

			rectLight.GetPrim().CreateAttribute(
				TfToken("intensity"), 
				SdfValueTypeNames->Float
    		).Set(15000.0f);

			rectLight.GetWidthAttr().Set(lightWidth);
			rectLight.GetHeightAttr().Set(lightHeight);

			// Projector box
			SdfPath cubePath = regionPath.AppendChild(TfToken("ProjectorBox"));
			UsdGeomCube projectorBoxMesh = UsdGeomCube::Define(stage, cubePath);
			
			const auto projectorBoxSize = GfVec3f(50, 15, 40);
			const auto projectorBoxOffset = GfVec3f(0, 0, 42);
			auto projectorBoxXform = UsdGeomXformable(projectorBoxMesh);
    		projectorBoxXform.AddTranslateOp(UsdGeomXformOp::PrecisionFloat).Set<GfVec3f>(projectorBoxOffset);
			projectorBoxXform.AddScaleOp(UsdGeomXformOp::PrecisionFloat).Set<GfVec3f>(projectorBoxSize);
		}
	}

    // Copy contents into output layer.
    layer->TransferContent(newLayer);

	return true;
}

bool MpcdiFileFormat::WriteToString(const SdfLayer& layer, std::string* str, const std::string& comment) const
{
	// this POC doesn't support writing
	return false;
}

bool MpcdiFileFormat::WriteToStream(const SdfSpecHandle& spec, std::ostream& out, size_t indent) const
{
	// this POC doesn't support writing
	return false;
}

/*
void MpcdiFileFormat::ComposeFieldsForFileFormatArguments(const std::string& assetPath, const PcpDynamicFileFormatContext& context, FileFormatArguments* args, VtValue* contextDependencyData) const
{
	 // Default sideLength.
    double sideLength = 1.0;

    VtValue value;
    if (!context.ComposeValue(MpcdiFileFormatTokens->SideLength,
                              &value) ||
        value.IsEmpty()) {

    }

    if (!value.IsHolding<double>()) {
        // error;
    }

    double length;

    (*args)[MpcdiFileFormatTokens->SideLength] = TfStringify(sideLength);
}

bool MpcdiFileFormat::CanFieldChangeAffectFileFormatArguments(const TfToken& field, const VtValue& oldValue, const VtValue& newValue, const VtValue& contextDependencyData) const
{
	// Check if the "sideLength" argument changed.
    double oldLength = oldValue.IsHolding<double>()
                           ? oldValue.UncheckedGet<double>()
                           : 1.0;
    double newLength = newValue.IsHolding<double>()
                           ? newValue.UncheckedGet<double>()
                           : 1.0;

    return oldLength != newLength;

}
*/
// these macros emit methods defined in the Pixar namespace
// but not properly scoped, so we have to use the namespace
// locally here
TF_DEFINE_PUBLIC_TOKENS(
	MpcdiFileFormatTokens,
	((Id, "mpcdiFileFormat"))
	((Version, "1.0"))
	((Target, "usd"))
	((Extension, "xml"))
	((SideLength, "Usd_Triangle_SideLength"))
);

TF_REGISTRY_FUNCTION(TfType)
{
	SDF_DEFINE_FILE_FORMAT(MpcdiFileFormat, SdfFileFormat);
}

PXR_NAMESPACE_CLOSE_SCOPE