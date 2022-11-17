cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerEHRReader)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/FHIRReader")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Stephen (Kitware), Ebrahim (Kitware), Andinet (Kitware)")
set(EXTENSION_DESCRIPTION "Read EHR data off a FHIR server. Currenlty reads Patient object and Observation Objects

Developed as part of the NIH Award R42HL145669 grant.")
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
