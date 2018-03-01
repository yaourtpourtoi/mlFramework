import root_pandas as rp
import ROOT as R
import root_numpy as rn
import copy
from array import array
R.gROOT.SetBatch(True)
R.gStyle.SetOptStat(0)

def main():

    version = "v1"
    channel = "tt"
    path = "/data/higgs/data_2016/ntuples_{0}/{1}/ntuples_SVFIT_merged/".format(version, channel)
    ext = "_{0}_{1}.root".format(channel,version)
    mcin = [
        (path + "BASIS_ntuple_GluGluHToTauTau_M125_powheg_MCSummer16"+ext,"ggH125"),
        (path + "BASIS_ntuple_VBFHToTauTau_M125_powheg_MCSummer16"+ext,"qqH125"),
        (path + "BASIS_ntuple_WXJets_merged_MCSummer16"+ext,"W"),
        (path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"DY"),
        (path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TT"),
        (path + "BASIS_ntuple_VV_MCSummer16"+ext,"VV"),
        (path + "BASIS_ntuple_EWKZ_merged_MCSummer16"+ext,"EWKZ"),
    ]
    datain = {
        "mt":(path + "BASIS_ntuple_SingleMuon"+ext,"data"),
        "et":(path + "BASIS_ntuple_SingleElectron"+ext,"data"),
        "tt":(path + "BASIS_ntuple_Tau"+ext,"data")
    }

    binning = {
        "eta_1": (50,-2.3,2.3),
        "eta_2": (50,-2.3,2.3),
        "pt_1": (100,20,220),
        "pt_2": (100,20,220),
        "jpt_1": (100,-10,220),
        "jpt_2": (100,-10,220),
        "jm_1": (100,-10,100),
        "jm_2": (100,-10,100),
        "jphi_1": (100,-10,5),
        "jphi_2": (100,-10,5),
        "bpt_1": (100,-10,220),
        "bpt_2": (100,-10,220),
        "beta_1": (100,-10,2.5),
        "beta_2": (100,-10,2.5),
        "njets": (12,0,12),
        "nbtag": (12,0,12),
        "mt_1": (100,0,150),
        "mt_2": (100,0,150),
        "pt_tt": (100,0,150),
        "m_sv": (100,0,300),
        "m_vis": (100,0,300),
        "mjj": (100,-10,150),
        "met": (100,0,150),
        "dzeta": (100,-100,150)

    }
    cuts = {"mt":"byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && iso_1 < 0.15 &&  !dilepton_veto  && passesThirdLepVeto && passesTauLepVetos && trg_singlemuon  ",
            "et":"byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && iso_1 < 0.1 &&  !dilepton_veto  && passesThirdLepVeto && passesTauLepVetos && trg_singleelectron  ",
            "tt": "byTightIsolationMVArun2v1DBoldDMwLT_1 > 0.5  && byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && passesThirdLepVeto && passesTauLepVetos && trg_doubletau"
            }
    cut = cuts[channel]
    weights = ["puweight","stitchedWeight","trk_sf","genweight","effweight","topWeight_run1","zPtReweightWeight"]
    scale = {"EWKZ":"1", "VV":"1","QCD_SS":"1","QCD":"1","DY":"1","qqH125":"10","ggH125":"10","W":"1","TT":"1"}
    lumi = "35.9"

    variables = [
        "pt_1",
        "pt_2",
        "eta_1",
        "eta_2",
        "bpt_1",
        "bpt_2",
        "beta_1",
        "beta_2",
        "jpt_1",
        "jpt_2",
        "jphi_1",
        "jphi_2",
        "jm_1",
        "jm_2",
        "njets",
        "nbtag",
        "mt_1",
        "mt_2",
        "pt_tt",
        "m_sv",
        "mjj",
        "m_vis",
        "met"
    ]
    variables = ["dzeta"]

    # histos= fillHistos(mcin, datain[channel], cut, weights, scale, "m_sv",binning, what = ["qqH125","EWKZ","ggH125","VV","QCD","TT","W","DY"])
    for var in variables:
        print "producing ", var
        histos= fillHistos(mcin, datain[channel], cut, weights, lumi, var,binning.get(var,(100,-50,50)), what = ["qqH125","ggH125","VV","QCD","TT","W","DY"])
        #makeNormalizedPlot( histos = histos, scale = scale, name =  var)
        makeStackedPlot( histos = histos,name = var)

def makeNormalizedPlot(histos, scale,name):

    cv = R.TCanvas("cv_single", "cv_single", 10, 10, 700, 600)
    R.gPad.SetTopMargin(0.08)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetBottomMargin(0.08)
    leg = R.TLegend(0.82, 0.08, 0.98, 0.92)

    stack =  R.THStack("stack", "")

    first = True
    maxVal = 0
    for hist in histos:
        if hist in ["data","stack","ratio","leg","QCD"]: continue

        tmp = copy.deepcopy( histos[hist] )
        tmp.SetFillStyle(0)
        tmp.SetLineWidth(2)

        tmp.SetLineColor( tmp.GetFillColor() )
        # tmp.SetFillColorAlpha(tmp.GetFillColor(), 0.1)
        tmp.GetXaxis().SetLabelFont(63)
        tmp.GetXaxis().SetLabelSize(14)
        tmp.GetYaxis().SetLabelFont(63)
        tmp.GetYaxis().SetLabelSize(14)
        print hist , float( scale.get(hist,1) )  / (tmp.Integral() ), tmp.Integral(), tmp.GetEntries() 
        tmp.Scale(  float( scale.get(hist,1) )  * float(tmp.GetEntries() ) / tmp.Integral()  )
        leg.AddEntry(tmp,hist)
        maxVal = max(maxVal, tmp.GetMaximum() )
        if first:
            dummy = copy.deepcopy(tmp)
        stack.Add(tmp)

    dummy.GetYaxis().SetRangeUser(0,maxVal*1.2)
    dummy.Draw("hist")
    stack.Draw("same nostack hist")
    leg.Draw()

    cv.Print("single_" +name+'.png')


def makeStackedPlot(histos, name):

    histos["data"].GetXaxis().SetNdivisions(0)


    cv= createRatioCanvas("cv")
  
    cv.cd(2)
    tmp = copy.deepcopy( histos["data"] )
    tmp.GetXaxis().SetLabelFont(63)
    tmp.GetXaxis().SetLabelSize(14)
    tmp.GetYaxis().SetLabelFont(63)
    tmp.GetYaxis().SetLabelSize(14)
    tmp.SetTitle("")
    tmp.GetYaxis().SetRangeUser( 0.1, 1000 )
    tmp.Draw("e1")
    histos["stack"].Draw("same HIST")
    tmp.Draw("same e1")
    

    cv.cd(1)
    histos["data"].GetYaxis().SetRangeUser(1000, max(histos["data"].GetMaximum(), histos["stack"].GetMaximum() )*1.20 )
    histos["ratio"].GetYaxis().SetNdivisions(5)
    histos["data"].GetXaxis().SetLabelFont(63)
    histos["data"].GetXaxis().SetLabelSize(14)
    histos["data"].GetYaxis().SetLabelFont(63)
    histos["data"].GetYaxis().SetLabelSize(14)
    histos["data"].Draw("e1")
    histos["stack"].Draw("same HIST")
    histos["data"].Draw("same e1")
    histos["leg"].Draw()
    # R.gPad.RedrawAxis()
    
    cv.cd(3)
    histos["ratio"].GetYaxis().SetRangeUser(0.5, 1.5)
    histos["ratio"].GetYaxis().SetNdivisions(6)
    histos["ratio"].GetXaxis().SetLabelSize(0.08)
    histos["ratio"].GetYaxis().SetLabelSize(0.08)
    histos["ratio"].GetXaxis().SetLabelOffset(0.02)
    histos["ratio"].GetYaxis().SetLabelOffset(0.01)
    histos["ratio"].Draw()

    cv.cd(2)
    R.gPad.RedrawAxis()

    cv.Print("test_" +name+'.png') 

 


def fillHistos(mcin, datain, cut, weights, lumi, variable, binning ,what = []):

    histos = {}

    for sample,name in mcin:

        tmp =   rp.read_root( paths = sample,
                              where = cut + "&& q_1*q_2 < 0",
                              columns = weights + [variable]  )


        tmp.eval( "eweight = " + "*".join( [lumi] + weights),  inplace = True )
        

        histos[name] = R.TH1D(variable + name,name,*(binning))

        histos[name].GetXaxis().SetLabelSize(0.08)
        histos[name].GetYaxis().SetLabelSize(0.08)
        histos[name].SetFillColor( getColor( name ) )
        histos[name].SetLineColor( R.kBlack )


        rn.fill_hist( histos[name], array = tmp[variable].values,
                                    weights = tmp["eweight"].values )
        # print histos[name].Integral(), name


#######################################################


    tmp =   rp.read_root( paths = datain[0],
                          where = cut+ "&& q_1*q_2 > 0",
                          columns = weights + [variable] )


    histos["QCD_SS"] = R.TH1D(variable + "QCD_SS","QCD_SS",*(binning))
    histos["QCD_SS"].Sumw2(True)
    histos["QCD_SS"].SetFillColor( getColor( "QCD" ) )
    histos["QCD_SS"].SetLineColor( R.kBlack )
    tmp.eval( "eweight = 1"  , inplace = True )

    rn.fill_hist( histos["QCD_SS"], array = tmp[variable].values,
                                 weights = tmp["eweight"].values)

    histos["QCD"] = copy.deepcopy( histos["QCD_SS"] )
    for sample,name in mcin:
        tmp =   rp.read_root( paths = sample,
                              where = cut + "&& q_1*q_2 > 0",
                              columns = weights + [variable]  )


        tmp.eval( "eweight = " + "*".join( [lumi] + weights) , inplace = True )


        tmp_SS = R.TH1D(variable + name+"SS",name+"SS",*(binning))

        rn.fill_hist( tmp_SS, array = tmp[variable].values,
                                    weights = tmp["eweight"].values )

        histos["QCD"].Add( tmp_SS, -1 )

    # print histos["QCD"].Integral(), "QCD"

#############################################
    tmp =   rp.read_root( paths = datain[0],
                          where = cut+ "&& q_1*q_2 < 0",
                          columns = weights + [variable] )
    tmp.eval( "eweight = 1"  , inplace = True )

    data = R.TH1D(variable + "data","data",*(binning))
    data.Sumw2(True)
    rn.fill_hist( data, array = tmp[variable].values,
                        weights = tmp["eweight"].values)


    leg = R.TLegend(0.82, 0.03, 0.98, 0.92)
    stack =  R.THStack("stack", "")
    ratio = R.TH1D(variable + "ratio","",*binning)

    leg.AddEntry(histos[ what[0] ] , what[0] )

    ratio.Add( histos[ what[0] ] )
    stack.Add( histos[ what[0] ] )
    for h in what[1:]:
        leg.AddEntry(histos[ h ] , h )
        stack.Add( histos[h] )
        ratio.Add( histos[h] )
    ratio.Divide(data)

    histos["ratio"] = copy.deepcopy( ratio )
    histos["stack"] = copy.deepcopy( stack )
    histos["data"] = copy.deepcopy( data )
    histos["leg"] = copy.deepcopy( leg )

    return histos



def createRatioCanvas(name, errorBandFillColor=14, errorBandStyle=3354 ):
    cv = R.TCanvas(name, name, 10, 10, 700, 600)

    # this is the tricky part...
    # Divide with correct margins
    cv.Divide(1, 3, 0.0, 0.0)

    # Set Pad sizes
    cv.GetPad(1).SetPad(0.0, 0.55, 1., 1.0)
    cv.GetPad(2).SetPad(0.0, 0.32, 1., 0.55)
    cv.GetPad(3).SetPad(0.0, 0.00, 1., 0.34)

    cv.GetPad(1).SetFillStyle(4000)
    cv.GetPad(2).SetFillStyle(4000)
    cv.GetPad(3).SetFillStyle(4000)

    # Set pad margins 1
    cv.cd(1)
    R.gPad.SetTopMargin(0.08)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetRightMargin(0.2)

    cv.cd(2)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetBottomMargin(0.03)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetLogy()

    # Set pad margins 2
    cv.cd(3)
    R.gPad.SetTopMargin(0.08)
    R.gPad.SetBottomMargin(0.35)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetGridy()

    cv.cd(1)
    

    return cv

def getColor(name):
    if name in ["TT","TTT","TTJ"]: return R.TColor.GetColor(155,152,204)
    if name in ["sig"]:            return R.kRed
    if name in ["bkg"]:            return R.kBlue
    if name in ["qqH125"]:         return R.kRed
    if name in ["ggH125"]:         return R.kBlue
    if name in ["W"]:              return R.TColor.GetColor(222,90,106)
    if name in ["VVT","VVJ","VV"]: return R.TColor.GetColor(88,211,247)
    if name in ["ZL","ZJ","ZLJ"]:  return R.TColor.GetColor(100,192,232)

    if name in ["QCD"]:            return R.TColor.GetColor(250,202,255)
    if name in ["ZTT","DY"]:       return R.TColor.GetColor(248,206,104)
    else: return R.kYellow

if __name__ == '__main__':
    main()