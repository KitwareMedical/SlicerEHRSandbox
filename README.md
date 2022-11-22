# SlicerEHRSandbox

*UNDER DEVELOPMENT*

Slicer extension for reading EHR data from a FHIR server. 

## How To Use

After the extension has been installed, swap to the FHIRReader module. The left side of the screen will have a FHIR url textbox with three selection menus below. The right side of the screen will have two empty tables for displaying patient information and observation information.

Before attempting to connect to a server, first check to see if your Slicer has the [fhirclient](https://pypi.org/project/fhirclient/) python module installed. If you do not you not know if it isntalled or if it is not installed, there is an advanced tab at the bottom of the screen that contains a button to install the module for you.

With fhirclient installed, type the url of the FHIR server to connect to into the FHIR url textbox. The URL should follow the format of `http://localhost:2400/hapi-fhir-jpaserver/`. It is important to note the url should end with `hapi-fhir-jpaserver`.

The system will begin to load all patients from the server. Depending on the amount of patients, it can take a few seconds to load all patients. The first selection menu will have the patients as options. The display string for each patient item will vary depending on the information available. If there are names on the server, each patient will be displayed as `Last Name, First Name`. If there are no names available, each patient will be displayed as `Patient **id**`. If this value is not present on the server, then the patient will be displayed as `Patient **number**` where **number** will increment with each patient.

Double clicking on a patient will display the information on the left table and load all observations associated with the patient. The observations will populate the second selection menu. The observations will be grouped by types found. Double clicking an observation type will populate the left table with all of the patient's observation of that type.

## FHIR Server

If you have data without a FHIR server, it is still possible to use the extension. Using (lungair-fhir-server)[https://github.com/KitwareMedical/lungair-fhir-server], it is possible to create a Docker container containing a FHIR server. Consult the README on how to convert your data into a FHIR server. Once the FHIR server has been created, you can use SlicerEHRSandbox as normal.


## License

This software is licensed under the terms of the [Apache Licence Version 2.0](LICENSE).

The license file was added at revision [1dea689](https://github.com/stephencrowell/fhir-slicer-extension/commit/1dea6896a48818de5dd017c82a31c5320fa9ed29) on 2022-11-17, but you may consider that the license applies to all prior revisions as well.