#START-FILE-LIST
# File List auto generated by waf2cmake.py, do not modify manually.

start_sources()
# -- resourcecompilerimage.waf_files --
sources_platform(ALL)
add_sources("NoUberFile"
	SOURCE_GROUP "CryCommonTools"
		"../../CryCommonTools/PathHelpers.cpp"
		"../../CryCommonTools/FileUtil.cpp"
		"../../CryCommonTools/PathHelpers.h"
		"../../CryCommonTools/FileUtil.h"
		"../../CryCommonTools/Metadata/Metadata.cpp"
		"../../CryCommonTools/Metadata/Metadata.h"
	SOURCE_GROUP "Root"
		"ResourceCompilerSubstance.cpp"
		"ResourceCompilerSubstance.h"
        "SubstanceConverter.cpp"
        "SubstanceConverter.h"
        "SubstanceCompiler.cpp"
        "SubstanceCompiler.h"
	SOURCE_GROUP "hidden"
		"../ResourceCompiler/IConfig.cpp"
		"../../CryCommonTools/StringHelpers.cpp"
		"../../CryCommonTools/SimpleBitmap.h"
		"stdafx.h"
		"stdafx.cpp"
		"../../CryCommonTools/SuffixUtil.h"
		"SubstanceExports.def"
		"../../CryCommonTools/Util.h"
)

sources_platform(WIN32)
add_sources("NoUberFile"
	SOURCE_GROUP "CryCommonTools"
		"../../CryCommonTools/FileUtil_windows.cpp"
)
sources_platform(LINUX)
add_sources("NoUberFile"
	SOURCE_GROUP "CryCommonTools"
		"../../CryCommonTools/FileUtil_posix.cpp"
)

end_sources()
#END-FILE-LIST

CryResourceCompilerModule(ResourceCompilerSubstance PCH "StdAfx.cpp" SOLUTION_FOLDER "RC")

set_libpath_flag()
target_include_directories( ${THIS_PROJECT} PRIVATE 
	"${CMAKE_SOURCE_DIR}/ResourceCompiler"
	"${CRYENGINE_SOURCE_DIR}/Code/Tools/CryCommonTools"
	"${SDK_DIR}/squish-ccr"
    "${SDK_DIR}/SubstanceEngines/include"
    "${CRYENGINE_SOURCE_DIR}/Code/Sandbox/Libs/CrySubstance")
target_link_libraries(${THIS_PROJECT} PRIVATE CrySubstance tiff)
use_substance()
target_compile_options(${THIS_PROJECT} PRIVATE /EHsc /GR)
target_compile_definitions(${THIS_PROJECT} PRIVATE -DCRY_SUBSTANCE_STATIC -DRESOURCECOMPILERSUBSTANCE_EXPORTS -DRESOURCE_COMPILER_SUBSTANCE)
# target_link_libraries(${THIS_PROJECT} PRIVATE delayimp tiff zlib)


set_target_properties(${THIS_PROJECT} PROPERTIES LINK_FLAGS "/DEF:SubstanceExports.def")


