from array import array

class Var():

    def __init__(self, var):
        self.config = {
            "pred_prob": {"binning": {"def": (8, array("d", [0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0] ) ) },           "tex":r"ML score"},
            "pred_class":{"binning": {"def": (8, -0.5,7.5 ) },   "tex":r"class"}, 
            "m_sv":      {"binning": {"def": (10,20,200) },  "tex":r"m_{sv}" },
            "m_vis":      {"binning": {"def": (10,20,200) },    "tex":r"m_{vis}" },                                            
            "eta_1":     {"binning": {"def": (10,-2.3,2.3) },     "tex":r"#eta_{1}" },
            "eta_2":     {"binning": {"def": (10,-2.3,2.3) }, "tex":r"#eta_{2}" },
            "iso_1":     {"binning": {"def": (100,0,0.1) },     "tex":r"iso_{1}" },
            "iso_2":     {"binning": {"def": (50,0,1) },     "tex":r"iso_{2}" },
            "pt_1":      {"binning": {"def": (10,20,200) },  "tex":r"p_{T,1}" },
            "pt_2":      {"binning": {"def": (10,20,200) },  "tex":r"p_{T,2}" },
            "jpt_1":     {"binning": {"def": (10,20,200) }, "tex":r"p_{T,1}^{jet}" },
            "jpt_2":     {"binning": {"def": (10,20,200) }, "tex":r"p_{T,2}^{jet}" },
            "jm_1":      {"binning": {"def": (10,2,30) }, "tex":r"m_{1}^{jet}" },
            "jm_2":      {"binning": {"def": (10,2,30) }, "tex":r"m_{2}^{jet}" },
            "jphi_1":    {"binning": {"def": (100,-10,5) },   "tex":r"#phi_{1}^{jet}" },
            "jphi_2":    {"binning": {"def": (100,-10,5) },   "tex":r"#phi_{2}^{jet}" },
            "dijetpt":   {"binning": {"def": (10,0,200) },   "tex":r"p_{T}^{j1,j2}" },            
            "bpt_1":     {"binning": {"def": (10,30,200) }, "tex":r"p_{T,1}^{b-jet}" },
            "bpt_2":     {"binning": {"def": (10,30,200) }, "tex":r"p_{T,2}^{b-jet}" },
            "bcsv_1":    {"binning": {"def": (10,0.6,1) },     "tex":r"b_{csv}^{1}" },
            "bcsv_2":    {"binning": {"def": (10,0.6,1) },     "tex":r"b_{csv}^{2}" },
            "beta_1":    {"binning": {"def": (100,-10,2.5) }, "tex":r"#eta_{1}^{b-jet}" },
            "beta_2":    {"binning": {"def": (100,-10,2.5) }, "tex":r"#eta_{2}^{b-jet}" },
            "njets":     {"binning": {"def": (5,array("d", [0,1,2,3,4,25])) },     "tex":r"N_{jet}" },
            "nbtag":     {"binning": {"def": (5,array("d", [0,1,2,3,4,25])) },     "tex":r"N_{b-tag}" },
            "mt_1":      {"binning": {"def": (10,0,80) },   "tex":r"m_{T,1}" },
            "mt_2":      {"binning": {"def": (10,0,100) },   "tex":r"m_{T,2}" },
            "pt_tt":     {"binning": {"def": (10,0,150) },   "tex":r"p_{T}^{#tau#tau}" },
            "pt_vis":     {"binning": {"def": (15,0,150) },   "tex":r"p_{T}^{#tau#tau}" },            
            "mjj":        {"binning": {"def": (10,10,150) }, "tex":r"m_{jj}" },
            "npv":        {"binning": {"def": (100,0,100) }, "tex":r"N_{PV}" },
            "met":        {"binning": {"def": (10,0,150) },   "tex":r"E_{T}^{miss}" },
            "dzeta":      {"binning": {"def": (100,-100,150) },"tex":r"D_{#zeta}" },
            "m_vis:njets":{"binning": {"def": (10,20,200,5,array("d", [0,1,2,3,4,15]) )  }, "tex":r"m_{vis} / N_{jet}" },
            "m_vis:mt_1": {"binning": {"def": (10,20,200,5,0,50 )  }, "tex":r"m_{vis} / m_{T,1}" },
        }


        self.set(var)

    def getBranches(self,for_df = False):
        if ":" in self.name: return self.name.split(":")
        if for_df: return [self.name]
        return self.name

    def is2D(self):
        if ":" in self.name: return True
        return False

    def set(self, var):

        if not self.config.get(var, False ):
            self.binning = {"def":(100,-50,50) }
            self.tex = var
            self.name = var

        else:
            self.binning = self.config[var]["binning"]
            self.tex = self.config[var]["tex"]
            self.name = var

    def bins(self, other = ""):

        if other:
            return self.binning.get(other, self.binning["def"] )
        return self.binning["def"]



