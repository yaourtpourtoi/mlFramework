from array import array

class Var():

    def __init__(self, var):
        self.config = {
            "pred_prob": {"binning": {"def": (8, array("d", [0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0] ) ) },           "tex":r"ML score"},
            "m_sv":      {"binning": {"def": (12, array("d", [0,40,60,70,80,90,100,110,120,130,150,200,250] )) },  "tex":r"m_{sv}" },
            "eta_1":     {"binning": {"def": (30,-3,3) },     "tex":r"#eta_{1}" },
            "eta_2":     {"binning": {"def": (50,-2.3,2.3) }, "tex":r"#eta_{2}" },
            "iso_1":     {"binning": {"def": (100,0,1) },     "tex":r"iso_{1}" },
            "iso_2":     {"binning": {"def": (100,0,1) },     "tex":r"iso_{2}" },
            "pt_1":      {"binning": {"def": (100,20,220) },  "tex":r"p_{T,1}" },
            "pt_2":      {"binning": {"def": (100,20,220) },  "tex":r"p_{T,2}" },
            "jpt_1":     {"binning": {"def": (100,-10,220) }, "tex":r"p_{T,1}^{jet}" },
            "jpt_2":     {"binning": {"def": (100,-10,220) }, "tex":r"p_{T,2}^{jet}" },
            "jm_1":      {"binning": {"def": (100,-10,100) }, "tex":r"m_{1}^{jet}" },
            "jm_2":      {"binning": {"def": (100,-10,100) }, "tex":r"m_{2}^{jet}" },
            "jphi_1":    {"binning": {"def": (100,-10,5) },   "tex":r"#phi_{1}^{jet}" },
            "jphi_2":    {"binning": {"def": (100,-10,5) },   "tex":r"#phi_{2}^{jet}" },
            "bpt_1":     {"binning": {"def": (100,-10,220) }, "tex":r"p_{T,1}^{b-jet}" },
            "bpt_2":     {"binning": {"def": (100,-10,220) }, "tex":r"p_{T,2}^{b-jet}" },
            "bcsv_1":    {"binning": {"def": (100,0,1) },     "tex":r"b_{csv}^{1}" },
            "bcsv_2":    {"binning": {"def": (100,0,1) },     "tex":r"b_{csv}^{2}" },
            "beta_1":    {"binning": {"def": (100,-10,2.5) }, "tex":r"#eta_{1}^{b-jet}" },
            "beta_2":    {"binning": {"def": (100,-10,2.5) }, "tex":r"#eta_{2}^{b-jet}" },
            "njets":     {"binning": {"def": (12,0,12) },     "tex":r"N_{jets}" },
            "nbtag":     {"binning": {"def": (12,0,12) },     "tex":r"N_{b-jets}" },
            "mt_1":      {"binning": {"def": (100,0,100) },   "tex":r"m_{T,1}" },
            "mt_2":      {"binning": {"def": (100,0,150) },   "tex":r"m_{T,2}" },
            "pt_tt":     {"binning": {"def": (100,0,150) },   "tex":r"p_{T}^{tot}" },

            "m_vis":     {"binning": {"def": (30,0,300) },    "tex":r"m_{vis}" },
            "mjj":       {"binning": {"def": (100,-10,150) }, "tex":r"m_{jj}" },
            "met":       {"binning": {"def": (100,0,150) },   "tex":r"E_{T}^{miss}" },
            "dzeta":     {"binning": {"def": (100,-100,150) },"tex":r"D_{#zeta}" }
        }


        self.set(var)

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



