cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerEHRSandbox)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/FHIRReader")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Stephen Crowell (Kitware), Ebrahim Ebrahim (Kitware), Andinet Enquobahrie (Kitware)")
set(EXTENSION_DESCRIPTION "Read EHR data off a FHIR server. Currently reads Patient object and Observation Objects

This work was supported by the National Institutes of Health under Award Number R42HL145669. The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health.")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/FHIRReader.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/FHIRReader/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(FHIRReader)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
