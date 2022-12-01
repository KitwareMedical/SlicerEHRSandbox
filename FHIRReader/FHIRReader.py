import logging
import os

import vtk
import ctk
import qt
import slicer
import requests
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

from Utils import BusyCursor
from Utils import DependencyInstaller
from dicomweb_client.api import DICOMwebClient

allowLoading = True

try:
    from fhirclient import client
    import fhirclient.models.observation as o
    import fhirclient.models.patient as p
    import fhirclient.models.bundle as b
except Exception as e:
    # We cannot use slicer.util.errorDisplay here because there is no main window (it will only log an error and not raise a popup).
    qt.QMessageBox.critical(
        slicer.util.mainWindow(), "Error importing fhirclient",
        "Error importing fhirclient. " +
        "If python dependencies are not installed, press the " +
        "\"Check for fhirclient install\" button under the " + 
        "Advanced tab. \n" +
        "Details: " + str(e)
    )
    allowLoading = False 

#
# FHIRReader
#

class FHIRReader(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "FHIRReader"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#FHIRReader">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#

def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # FHIRReader1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='FHIRReader',
        sampleName='FHIRReader1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'FHIRReader1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='FHIRReader1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='FHIRReader1'
    )

    # FHIRReader2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='FHIRReader',
        sampleName='FHIRReader2',
        thumbnailFileName=os.path.join(iconsPath, 'FHIRReader2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='FHIRReader2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='FHIRReader2'
    )

#
# FHIRReaderWidget
#

class FHIRReaderWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False
        self.patient_table_node = None
        self.observations_table_node = None

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/FHIRReader.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        slicer.util.setDataProbeVisible(False)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = FHIRReaderLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        advancedCollapsible = ctk.ctkCollapsibleButton()
        advancedCollapsible.text = "Advanced"
        self.layout.addWidget(advancedCollapsible)
        advancedLayout = qt.QFormLayout(advancedCollapsible)
        advancedCollapsible.collapsed = True

        def add_install_button(package_name: str, install_function: str):
            installButton = qt.QPushButton(f"Check for {package_name} install")
            installButton.clicked.connect(lambda unused_arg: install_function())
            advancedLayout.addRow(installButton)


        add_install_button("fhirclient", DependencyInstaller.check_and_install_fhirclient)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.FhirServerLineEdit.connect("valueChanged(str)", self.updateParameterNodeFromGUI)
        self.ui.DICOMLineEdit.connect("valueChanged(str)", self.updateParameterNodeFromGUI)
        self.ui.PatientListWidget.itemDoubleClicked.connect(self.onPatientListWidgetDoubleClicked)
        self.ui.ObservationListWidget.itemDoubleClicked.connect(self.onObservationListWidgetDoubleClicked)

        # Buttons
        self.ui.loadPatientsButton.connect('clicked(bool)', self.onLoadPatientsButton)
        self.ui.loadDICOMButton.connect('clicked(bool)', self.onLoadDICOMButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        self.patient_table_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
        self.patient_table_node.SetName("PatientInfo_TableNode")

        self.observation_table_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
        self.observation_table_node.SetName("ObservationInfo_TableNode")

        with open(self.resourcePath('fhir-layout.xml')) as fh:
            layout_text = fh.read()

        layoutID = 5001

        layoutManager = slicer.app.layoutManager()
        layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(layoutID, layout_text)

        for i in range(layoutManager.tableViewCount):
            tableWidget = layoutManager.tableWidget(i)
            tableController = tableWidget.tableController()
            tableController.pinButton().hide()
            
            if tableWidget.name == 'qMRMLTableWidgetPatientInformation':
                tableWidget.tableView().setMRMLTableNode(self.patient_table_node)
            elif tableWidget.name == 'qMRMLTableWidgetPatientObservations':
                tableWidget.tableView().setMRMLTableNode(self.observation_table_node)

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()


        layoutManager = slicer.app.layoutManager()
        self.oldLayout = layoutManager.layout

        # set the layout to be the current one
        layoutManager.setLayout(5001)

        for i in range(layoutManager.tableViewCount):
            tableWidget = layoutManager.tableWidget(i)
            
            if tableWidget.name == 'qMRMLTableWidgetPatientInformation':
                tableWidget.tableView().setMRMLTableNode(self.patient_table_node)
            elif tableWidget.name == 'qMRMLTableWidgetPatientObservations':
                tableWidget.tableView().setMRMLTableNode(self.observation_table_node)

        

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        layoutManager = slicer.app.layoutManager()

        layoutManager.setLayout(self.oldLayout)


    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())


    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.loadPatientsButton.enabled = allowLoading

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.EndModify(wasModified)

    def onLoadPatientsButton(self):
        """
        Run processing when user clicks "Load Patients" button.
        """
        with BusyCursor.BusyCursor():
            self.logic.fetchPatients(self.ui.FhirServerLineEdit.text)
            self.loadPatients()

    def loadPatients(self):
        self.ui.PatientListWidget.clear()
        self.ui.ObservationListWidget.clear()
        for idx, patient in enumerate(self.logic.patients):
            item = qt.QListWidgetItem()
            item.setData(21, idx)
            if (patient.name is not None):
                item.setText('{0}, {1}'.format(patient.name[0].family, patient.name[0].given[0]))
            elif (patient.identifier is not None):
                item.setText('Patient {0}'.format(patient.identifier[0].value))
            else:
                item.setText('Patient {0}'.format(patient.id))
            self.ui.PatientListWidget.addItem(item)

    def onPatientListWidgetDoubleClicked(self, item):
        with BusyCursor.BusyCursor():
            self.observation_table_node.RemoveAllColumns()
            self.loadPatientInfo(item.data(21))
            self.loadPatientObservations(item.data(21))

    def loadPatientObservations(self, idx):
        self.ui.ObservationListWidget.clear()
        patient = self.logic.patients[idx]
        self.logic.getObservations(patient)
        for observationType in list(self.logic.selectedObservations.keys())[1:]:
            item = qt.QListWidgetItem()
            item.setData(21, observationType)
            item.setText('{0}'.format(observationType))
            self.ui.ObservationListWidget.addItem(item)

    def onObservationListWidgetDoubleClicked(self, item):
        observationType = item.data(21)
        self.observation_table_node.RemoveAllColumns()        

        column_names = ['id', 'Value', 'Unit', 'Observation Type', 'Date','UCUM Code', 'Code Value',
            'Code System', 'Identifier System', 'Identifier Value']
    

        for column_name in column_names:
            columnArray = vtk.vtkStringArray()
            columnArray.SetName(column_name)
            for observation in self.logic.selectedObservations[observationType]:
                if (column_name == 'id'):
                    columnArray.InsertNextValue(observation.id)
                elif (column_name == 'Value'):
                    columnArray.InsertNextValue(str(observation.valueQuantity.value))
                elif (column_name == 'Unit'):
                    columnArray.InsertNextValue(str(observation.valueQuantity.unit))
                elif (column_name == 'Observation Type'):
                    columnArray.InsertNextValue(observation.code.coding[0].display)
                elif (column_name == 'Date'):
                    columnArray.InsertNextValue(observation.effectiveDateTime.date.strftime('%Y-%m-%d %H:%M:%S.%f')
                            if observation.effectiveDateTime is not None else "")
                elif (column_name == 'UCUM Code'):
                    columnArray.InsertNextValue(str(observation.valueQuantity.code))
                elif (column_name == 'Code Value'):
                    columnArray.InsertNextValue(observation.code.coding[0].code)
                elif (column_name == 'Code System'):
                    columnArray.InsertNextValue(observation.code.coding[0].system)
                elif (column_name == 'Identifier System'):
                    columnArray.InsertNextValue(observation.identifier[0].system if observation.identifier is not None else "")
                elif (column_name == 'Identifier Value'):
                    columnArray.InsertNextValue(observation.identifier[0].value if observation.identifier is not None else "")

            self.observation_table_node.AddColumn(columnArray)

        # observation_table_node.SetLocked(True);

    def loadPatientInfo(self, idx):
        self.patient_table_node.RemoveAllColumns()

        column_names = ['id', 'Gender', 'First Name', 'Last Name', 'Date of Birth', 'Identifier System', 'Identifier Value']
        
        labelArray = vtk.vtkStringArray()
        valueArray = vtk.vtkStringArray()

        for column_name in column_names:
            labelArray.InsertNextValue(column_name)

        self.patient_table_node.AddColumn(labelArray)

        patient = self.logic.patients[idx]

        valueArray.InsertNextValue(patient.id)
        valueArray.InsertNextValue(patient.gender)
        valueArray.InsertNextValue(patient.name[0].given[0])
        valueArray.InsertNextValue(patient.name[0].family)
        valueArray.InsertNextValue(patient.birthDate.date.strftime('%Y-%m-%d') if patient.birthDate is not None else "")
        valueArray.InsertNextValue(patient.identifier[0].system if patient.identifier is not None else "")
        valueArray.InsertNextValue(patient.identifier[0].value if patient.identifier is not None else "")

        self.patient_table_node.AddColumn(valueArray)

    def onLoadDICOMButton(self):
        """
        Run processing when user clicks "Load Patients" button.
        """

        self.logic.fetchDICOM(self.ui.DICOMLineEdit.text)
        
#
# FHIRReaderLogic
#

class FHIRReaderLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        self.patients = []
        self.selectedObservations = {}
        self.fhirURL = ""
        self.dicomURL = ""

        self.patient_table_view = None
        self.observations_table_view = None     

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """

    def fetchPatients(self, fhirUrl):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param fhirUrl: fhir server to connect to
        """            
        if (len(fhirUrl) == 0):
            slicer.util.errorDisplay('Error intializing FHIR Client. Is FHIR Server empty?', windowTitle='Error')
            return

        self.fhirURL = fhirUrl if (fhirUrl[-1] == '/') else fhirUrl + '/'
        settings = {
            'app_id': 'my_web_app',
            'api_base': self.fhirURL + "fhir/"
        }
        try:
            self.smart = client.FHIRClient(settings=settings)
        except BaseException as e:
            slicer.util.errorDisplay('Error intializing FHIR Client. Does the server exist at {0} ?'.format(self.fhirURL), windowTitle='Error')
            return

        try:
            self.smart.server.request_json('Patient')
        except BaseException as e:
            slicer.util.errorDisplay('Error connecting to FHIR Server. Does the server exist at {0} ?'.format(self.fhirURL), windowTitle='Error')
            return
        
        search = p.Patient.where(struct={'_count': '200'})
        self.patients = self.performSearch(search) #search.perform_resources(self.smart.server)        

    def performSearch(self, search):
        try:
            bundle = search.perform(self.smart.server)
        except BaseException as e:
            slicer.util.errorDisplay('Error occured while communicating with FHIR Server.', windowTitle='Error')
            return []
        settings = {
            'app_id': 'my_web_app',
            'api_base': self.fhirURL
        }
        smart = client.FHIRClient(settings=settings)
        resources = []
        while(True):
            if bundle is not None and bundle.entry is not None:
                for entry in bundle.entry:
                    resources.append(entry.resource)
            if(len(bundle.link) <= 1 or bundle.link[1].relation != 'next'):
                break
            try:
                res = smart.server.request_json(bundle.link[1].url.split('/')[-1])
            except BaseException as e:
                slicer.util.errorDisplay('Error occured while communicating with FHIR Server.', windowTitle='Error')
                return []
            bundle = b.Bundle(res)

        return resources

    def getObservations(self, patient):
        search = o.Observation.where(struct={'subject': str(patient.id), '_count': '200'})
        self.selectedObservations = {}
        self.selectedObservations['all'] = self.performSearch(search)
        for observation in self.selectedObservations['all']:
            observationType = observation.code.coding[0].display
            if (observationType not in self.selectedObservations):
                self.selectedObservations[observationType] = []
            self.selectedObservations[observationType].append(observation)       

    def fetchDICOM(self, dicomUrl):
        self.dicomURL = dicomUrl[:-1] if (dicomUrl[-1] == '/') else dicomUrl
        client = DICOMwebClient(url=self.dicomURL)

        with BusyCursor.BusyCursor():
            response = client.search_for_studies(search_filters={'PatientID': 1})
        print(len(response))


#
# FHIRReaderTest
#

class FHIRReaderTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_FHIRReader1()

    def test_FHIRReader1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        self.delayDisplay('Test passed')
