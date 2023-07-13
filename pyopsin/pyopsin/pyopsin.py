import jpype
import jpype.imports
from jpype.types import *

class NameToSmiles:
    
    def __init__(self, path, 
                       allowUninterpretableStereo=False, 
                       allowRadicals=False,
                       wildcardRadicals=False,
                       allowAcidsWithoutAcid=False,):
        self.path = path

        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[self.path])
        from uk.ac.cam.ch.wwmm import opsin

        self.config = opsin.NameToStructureConfig()
        if allowUninterpretableStereo:
            self.config.setWarnRatherThanFailOnUninterpretableStereochemistry(True)
        if allowRadicals:
            self.config.setAllowRadicals(True)
        if allowAcidsWithoutAcid:
            self.config.setInterpretAcidsWithoutTheWordAcid(True)
        if wildcardRadicals:
            self.config.setOuputRadicalsAsWildCardAtoms(True)
        
        self.nts = opsin.NameToStructure.getInstance()


    def name_to_smiles(self, name):

        results = self.nts.parseChemicalName(name, self.config)
        return results.getSmiles()
    
    def name_to_cml(self, name):

        results = self.nts.parseChemicalName(name, self.config)
        return results.getCml()


if __name__ == "__main__":
    pass
    #### example use ####
    """
    nts = NameToSmiles("E:\PhD\cde_application\pyopsin\opsin_cli.jar", allowUninterpretableStereo=True,)
    name = "2,4,6-trinitrotoluene"
    smiles = nts.name_to_smiles(name)
    cml = nts.name_to_cml(name)
    print(smiles)
    print(cml)
    """
