# SlicerEHRSandbox

*UNDER DEVELOPMENT*

Slicer extension for reading EHR data from a FHIR server and DICOM data from a DICOMweb server. 

## Tutorial

0. `SlicerEHRSandbox` requires a FHIR server and a DICOMweb server. If you are missing either, go to the [FHIR Server](#fhirserver) section for a missing FHIR server and the [DICOMweb Server](#dicomwebserver) section for a missing DICOMweb server.
1. Place the url of your FHIR server into the FHIR Server textbox and (if available) place the url of your DICOMweb server into the DICOMweb server textbox. It is important to note the url should end with `hapi-fhir-jpaserver`.
2. Press the `Connect and Load Patients` button.
3. The `Patient Browser` list will be populated with all patients in the FHIR server. Double click a patient to load observations and DICOM studies.
4. The `Patient Information` table (left table) will populate with patient information from the FHIR server. The `Observation Browser` and `DICOM Browser` will populate with associated observation types and DICOM studies respectively.
5. Double click an obervation type. The `Patient Observations` table (right table) will populate with all observations of the selected type.
6. Double click a DICOM series. The `Patient DICOM` slice viewer will display the DICOM image after it is downloaded from the server. 

## <a name="fhirserver"></a>FHIR Server

If you have data without a FHIR server, it is still possible to use the extension. Using [lungair-fhir-server](https://github.com/KitwareMedical/lungair-fhir-server), it is possible to create a Docker container containing a FHIR server. Consult the README on how to convert your data into a FHIR server. Once the FHIR server has been created, you can use SlicerEHRSandbox as normal.

## <a name="dicomwebserver"></a>DICOMweb Server

If you have DICOM data without a DICOMweb server, it is possible to create a DICOMweb server using Slicer using the following steps.

1. Open another instance of Slicer.
2. Go to the `Add DICOM Data` module.
3. Press the `Import DICOM Data` button and select the directory with all DICOM files.
4. Go to the `Web Server` module.
5. Ensure the `DICOMweb API` box is checked in the `Advanced` tab.
6. Press the `Start Server` button.
7. Press the `Open static pages in external browser` button. This will give you url the web server is hosted at.
8. Add `/dicom` to the end of the url for the DICOM endpoint. This will be the url to put in the DICOMweb server textbox.

Please note that the `Patient ID` value in Slicer's DICOM database needs to be the same ID value in the first identifier value inside the the FHIR server. More information about identifier can be found [here](https://www.hl7.org/fhir/datatypes.html#Identifier). If the values do not match up:

1. Load the affected patient's series into Slicer.
2. Delete the same patients from the DICOM database.
3. Right click each series and select `Export to DICOM...`.
4. Change the `PatientID` value to match the value in FHIR.
5. Press the `Export` button.
6. Repeat for all series.

You can the continue from step 4 in the first set of DICOMweb server instructions.


## License

This software is licensed under the terms of the [Apache Licence Version 2.0](LICENSE).

The license file was added at revision [1dea689](https://github.com/stephencrowell/fhir-slicer-extension/commit/1dea6896a48818de5dd017c82a31c5320fa9ed29) on 2022-11-17, but you may consider that the license applies to all prior revisions as well.

