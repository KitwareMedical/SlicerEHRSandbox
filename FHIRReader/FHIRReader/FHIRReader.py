import logging
import os

import vtk
import ctk
import qt
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

from fhirclient import client
import fhirclient.models.observation as o
import fhirclient.models.patient as p


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

class ClinicalParametersTabWidget(qt.QTabWidget):  # TODO move this class to an appropriate place
    def __init__(self):
        super().__init__()

        self.patient_table_view = slicer.qMRMLTableView()
        self.patient_table_view.setMRMLScene(slicer.mrmlScene)
        # self.addTab(self.patient_table_view, "Patient data")
        self.patient_table_node = None  # vtkMRMLTableNode

    def set_table_node(self, table_node):
        """Set the patient table view to show the given vtkMRMLTableNode."""
        self.patient_table_view.setMRMLTableNode(table_node)
        self.patient_table_view.setFirstRowLocked(True)  # Put the column names in the top header, rather than A,B,...

    def set_patient_df(self, patient_df):
        """Populate the patient table view with the contents of the given dataframe"""
        if self.patient_table_node is not None:
            slicer.mrmlScene.RemoveNode(self.patient_table_node)
        self.patient_table_node = tableNodeFromDataFrame(patient_df, editable=False)
        self.patient_table_node.SetName("ClinicalParamatersTabWidget_PatientTableNode")
        self.set_table_node(self.patient_table_node)

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

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = FHIRReaderLogic()

        self.logic.setup(self.resourcePath('fhir-layout.xml'))

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.FhirServerLineEdit.connect("valueChanged(str)", self.updateParameterNodeFromGUI)
        self.ui.PatientListWidget.itemDoubleClicked.connect(self.onPatientListWidgetDoubleClicked)
        # self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        # self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        # self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        # self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        # self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

        # Buttons
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

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

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

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

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        # if not self._parameterNode.GetNodeReference("InputVolume"):
        #     firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        #     if firstVolumeNode:
        #         self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

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
        self.ui.FhirServerLineEdit.text = str(self._parameterNode.GetParameter("FHIRURL"))
        # self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
        # self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        # self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        # self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
        # self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

        # Update buttons states and tooltips
        # if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
        #     self.ui.applyButton.toolTip = "Compute output volume"
        self.ui.applyButton.enabled = True
        # else:
        #     self.ui.applyButton.toolTip = "Select input and output volume nodes"
        #     self.ui.applyButton.enabled = False

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

        self._parameterNode.SetParameter("FHIRURL", self.ui.FhirServerLineEdit.text)
        # self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
        # self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        # self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
        # self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
        # self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        self.logic.process(self.ui.FhirServerLineEdit.text)
        self.loadPatients()
        # self.ui.label.text = 'Cringe'
        # with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

        #     # Compute output
        #     self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
        #                        self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

        #     # Compute inverted output (if needed)
        #     if self.ui.invertedOutputSelector.currentNode():
        #         # If additional output volume is selected then result with inverted threshold is written there
        #         self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
        #                            self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

    def loadPatients(self):
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
        self.logic.loadPatientInfo(item.data(21))
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
        self.observations = []

        self.patient_browser_widget = None
        self.patient_observations_widget = None

    def setup(self, layout_file_path):
        with open(layout_file_path) as fh:
            layout_text = fh.read()

        layoutID = 5001

        layoutManager = slicer.app.layoutManager()
        layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(layoutID, layout_text)

        # set the layout to be the current one
        layoutManager.setLayout(layoutID)


        self.patient_table_node = None


        for i in range(layoutManager.plotViewCount):
            plotWidget = layoutManager.plotWidget(i)
            if plotWidget.name == 'qMRMLPlotWidgetPatientBrowser':
                self.patient_browser_widget = plotWidget
            elif plotWidget.name == 'qMRMLPlotWidgetPatientObservations':
                self.patient_observations_widget = plotWidget

        self.patient_browser_widget.layout().itemAt(1).widget().setParent(None)
        self.patient_observations_widget.layout().itemAt(1).widget().setParent(None)


        self.patient_table_view = slicer.qMRMLTableView()
        self.patient_table_view.setMRMLScene(slicer.mrmlScene)

        self.patient_browser_widget.layout().addWidget(self.patient_table_view)


        self.observations_table_view = slicer.qMRMLTableView()
        self.observations_table_view.setMRMLScene(slicer.mrmlScene)

        self.patient_observations_widget.layout().addWidget(self.observations_table_view)

        

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """

    def process(self, fhir_url):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        # array = vtk.vtkIntArray()
        # array.SetName('Col 1')

        # for i in range(10):
        #     array.InsertNextValue(i)

        # patient_table_node.AddColumn(array)

        # patient_table_node.SetLocked(True);

        # patient_table_node.SetName("PatientBrowser_TableNode")
        # self.patient_table_view.setMRMLTableNode(patient_table_node)
        # self.patient_table_view.setFirstRowLocked(True) 
        settings = {
            'app_id': 'my_web_app',
            'api_base': fhir_url
        }
        smart = client.FHIRClient(settings=settings)
        
        search = p.Patient.where(struct={})
        self.patients = search.perform_resources(smart.server)

        # self.loadPatients()

        print("Num of patients: {0}".format(len(self.patients)))

        search = o.Observation.where(struct={})
        self.observations = search.perform_resources(smart.server)


        print("Num of observations: {0}".format(len(self.observations)))

    def loadPatientInfo(self, idx):
        patient_table_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
        column_names = ['id', 'Gender', 'First Name', 'Last Name', 'Date of Birth', 'Identifier System', 'Identifier Value']
        columns = {}

        for column_name in column_names:
            array = vtk.vtkStringArray()
            array.SetName(column_name)
            array.Resize(len(self.patients))
            columns[column_name] = array

        patient = self.patients[idx]

        for column_name in column_names:
            if (column_name == 'id'):
                columns[column_name].InsertNextValue(patient.id)
            elif (column_name == 'Gender'):
                columns[column_name].InsertNextValue(patient.gender)
            elif (column_name == 'First Name'):
                columns[column_name].InsertNextValue(patient.name[0].given[0])
            elif (column_name == 'Last Name'):
                columns[column_name].InsertNextValue(patient.name[0].family)
            elif (column_name == 'Date of Birth'):
                columns[column_name].InsertNextValue(patient.birthDate.date.strftime('%Y-%m-%d'))
            elif (column_name == 'Identifier System'):
                columns[column_name].InsertNextValue(patient.identifier[0].system)
            elif (column_name == 'Identifier Value'):
                columns[column_name].InsertNextValue(patient.identifier[0].value)

        for column in columns:
            patient_table_node.AddColumn(columns[column])

        patient_table_node.SetLocked(True);

        patient_table_node.SetName("PatientBrowser_TableNode")
        self.patient_table_view.setMRMLTableNode(patient_table_node)
        self.patient_table_view.setFirstRowLocked(True)
        


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

        # # Get/create input data

        # import SampleData
        # registerSampleData()
        # inputVolume = SampleData.downloadSample('FHIRReader1')
        # self.delayDisplay('Loaded test data set')

        # inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(inputScalarRange[0], 0)
        # self.assertEqual(inputScalarRange[1], 695)

        # outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        # threshold = 100

        # # Test the module logic

        # logic = FHIRReaderLogic()

        # # Test algorithm with non-inverted threshold
        # logic.process(inputVolume, outputVolume, threshold, True)
        # outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        # self.assertEqual(outputScalarRange[1], threshold)

        # # Test algorithm with inverted threshold
        # logic.process(inputVolume, outputVolume, threshold, False)
        # outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        # self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')
