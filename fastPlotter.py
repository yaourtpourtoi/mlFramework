import root_pandas as rp
import ROOT as R
import root_numpy as rn
import copy
import sys
import os
from array import array
R.gROOT.SetBatch(True)
R.gStyle.SetOptStat(0)

def main():
    if not os.path.exists("plots"):
        os.mkdir("plots")
    if not os.path.exists("plots/Xcheck"):
        os.mkdir("plots/Xcheck")

    version = "v2"
    channel = "tt"
    svfit = "woSVFIT"


    mcin, datain, asimov= getMergedSamples(channel, version, svfit)
    what = ["VVT","VVJ","TTT","TTJ","W","ZJ","ZL","ZTT","QCD"]
    what.sort()

    # check = "W"
    # mcin, datain, asimov= getXCheck( check = check, channel = channel, vs = ["v1","v2"], svfit = svfit)
    # what = [check]


    binning = {
        "eta_1": (15,-3,3),
        "iso_1": (100,0,1),
        "iso_2": (100,0,1),
        "eta_2": (15,-3,3),
        "pt_1": (20,20,100),
        "pt_2": (5,30,230),
        "jpt_1": (100,-10,220),
        "jpt_2": (100,-10,220),
        "jm_1": (100,-10,100),
        "jm_2": (100,-10,100),
        "jphi_1": (100,-10,5),
        "jphi_2": (100,-10,5),
        "bpt_1": (100,-10,220),
        "bpt_2": (100,-10,220),
        "bcsv_1": (100,0,1),
        "bcsv_2": (100,0,1),
        "jcsv_1": (100,0,1),
        "jcsv_2": (100,0,1),
        "beta_1": (100,-10,2.5),
        "beta_2": (100,-10,2.5),
        "njets": (12,0,12),
        "nbtag": (12,0,12),
        "mt_1": (20,0,100),
        "mt_2": (100,0,150),
        "pt_tt": (100,0,150),
        "m_sv": (30,0,300),
        "m_vis": (20,0,200),
        "mjj": (100,-10,150),
        "met": (100,0,150),
        "trg_mutaucross": (1,0.5,1.5),
        "met_centrality":(100,-2,2),
        "sphericity":(100,0,1),
        "dzeta": (100,-100,150)

    }
    cuts = {"mt": "byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && iso_1 < 0.15 && mt_1 < 50 && !dilepton_veto  && passesThirdLepVeto && passesTauLepVetos && ( (trg_singlemuon && pt_1 > 23 && pt_2 > 30) || trg_mutaucross && pt_1 <= 23 && pt_2 > 30 ) ",
            "et": "byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && iso_1 < 0.1 && mt_1 < 50  && !dilepton_veto  && passesThirdLepVeto && passesTauLepVetos && trg_singleelectron  ",
            "tt": "byTightIsolationMVArun2v1DBoldDMwLT_1 > 0.5 && byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && passesThirdLepVeto && passesTauLepVetos && trg_doubletau "
            }
    cut = cuts[channel]
    weights = ["puweight","stitchedWeight","trk_sf","genweight","effweight","topWeight_run1","zPtReweightWeight","antilep_tauscaling"]
    scale = {"EWKZ":"1", "VV":"1","QCD_SS":"1","QCD":"1","DY":"1","qqH125":"10","ggH125":"10","W":"1","TT":"1"}
    lumi = "35.9"
    region = "os"


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
    if len(sys.argv) == 2:
        variables = [ sys.argv[1] ]
    elif len(sys.argv) == 3:
        variables = [ sys.argv[1] ]
        region = sys.argv[2] 


    # histos= fillHistos(mcin, datain[channel], cut, weights, scale, "m_sv",binning, what = ["qqH125","EWKZ","ggH125","VV","QCD","TT","W","DY"])
    for var in variables:
        print "producing ", var
        histos= fillHistos(channel, mcin, datain, cut, region, weights, lumi, var,binning.get(var,(100,-50,50)), what = what, asimov = asimov )
        #makeNormalizedPlot( histos = histos, scale = scale, name =  var)
        makeStackedPlot( histos = histos, name = var)
        saveToFile(histos = histos, name = var, channel = channel)

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

    histos["data"].GetXaxis().SetLabelSize(0)


    cv= createRatioCanvas("cv")
    maxVal = max(histos["data"].GetMaximum(), histos["stack"].GetMaximum() )*1.10
    cv.cd(2)
    tmp = copy.deepcopy( histos["data"] )
    tmp.GetXaxis().SetLabelSize(0)
    tmp.GetYaxis().SetLabelFont(63)
    tmp.GetYaxis().SetLabelSize(14)
    tmp.SetTitle("")
    tmp.GetYaxis().SetRangeUser( 0.1, maxVal / 100 )
    tmp.Draw("e1")
    histos["stack"].Draw("same HIST")
    tmp.Draw("same e1")
    

    cv.cd(1)
    histos["data"].GetYaxis().SetRangeUser(maxVal / 100,  maxVal)
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

    cv.Print("plots/Xcheck/" +name+'.png') 

def saveToFile(histos, name, channel):

    rfile = R.TFile( "htt_{channel}.inputs_sm_{var}.root".format(channel = channel, var = name) ,"RECREATE" )
    rdir = "{channel}_inclusive".format(channel = channel)
    rfile.mkdir(rdir)

    for hist in histos:
        if hist in ["ratio","leg","stack"]: continue
        rfile.cd(rdir)
        histos[hist].Write()
    rfile.Close()


def fillHisto(path, select, var, weights, lumi, name, binning, weight = True):

        tmp =   rp.read_root( paths = path,
                              where = select,
                              columns = weights + [var]  )

        if weight:
            if name == "ZTT": tmp.eval( "eweight = " + "*".join( ["34.1"] + weights),  inplace = True )
            else: tmp.eval( "eweight = " + "*".join( [lumi] + weights),  inplace = True )
        else:        
            tmp.eval( "eweight = 1"  , inplace = True )

        tmpHist = R.TH1D(name,name,*(binning))

        tmpHist.GetXaxis().SetLabelFont(63)
        tmpHist.GetXaxis().SetLabelSize(14)
        tmpHist.GetYaxis().SetLabelFont(63)
        tmpHist.GetYaxis().SetLabelSize(14)
        tmpHist.SetFillColor( getColor( name ) )
        tmpHist.SetLineColor( R.kBlack )
        tmpHist.Sumw2(True)

        rn.fill_hist( tmpHist, array = tmp[var].values,
                               weights = tmp["eweight"].values )

        return tmpHist

def fillHistos(channel, mcin, datain, cut,region, weights, lumi, variable, binning , what = [], asimov = False):

    histos = {}
    if region == "os":
        sign_cut = "&& q_1*q_2 < 0"
    else:
        sign_cut = "&& q_1*q_2 > 0"
    qcd_cut = "&& q_1*q_2 > 0"
    for sample,name,addcut in mcin:

        print "Loading ", name
        histos[name] = fillHisto(sample, cut + sign_cut + addcut, variable, weights, lumi, name, binning)
        # print histos[name].Integral(), name


#######################################################
    if "QCD" in what:
        print "Estimating QCD"
        if channel != "tt":

            histos["QCD"] = fillHisto(datain[0], cut+ qcd_cut, variable, weights, lumi, "QCD", binning, weight = False)
            for sample,name,addcut in mcin:
                if not name in what: continue
                tmp_SS = fillHisto(sample, cut + qcd_cut + addcut, variable, weights, lumi, name+"SS", binning, weight = True)
                histos["QCD"].Add( tmp_SS, -1 )
        else:
            # regions = {
            #     "B":"&& ((byTightIsolationMVArun2v1DBoldDMwLT_1 && byLooseIsolationMVArun2v1DBoldDMwLT_2 && !byTightIsolationMVArun2v1DBoldDMwLT_2) || (byTightIsolationMVArun2v1DBoldDMwLT_2 && byLooseIsolationMVArun2v1DBoldDMwLT_1 && !byTightIsolationMVArun2v1DBoldDMwLT_1)) && q_1*q_2 < 0",
            #     "C":"&& byTightIsolationMVArun2v1DBoldDMwLT_1 > 0.5 && byTightIsolationMVArun2v1DBoldDMwLT_2 > 0.5 && q_1*q_2 > 0",
            #     "D":"&& ((byTightIsolationMVArun2v1DBoldDMwLT_1 && byLooseIsolationMVArun2v1DBoldDMwLT_2 && !byTightIsolationMVArun2v1DBoldDMwLT_2) || (byTightIsolationMVArun2v1DBoldDMwLT_2 && byLooseIsolationMVArun2v1DBoldDMwLT_1 && !byTightIsolationMVArun2v1DBoldDMwLT_1)) && q_1*q_2 > 0",
            # }

            regions = {
                "B":"&& ( (byTightIsolationMVArun2v1DBoldDMwLT_1 && byLooseIsolationMVArun2v1DBoldDMwLT_2 && !byTightIsolationMVArun2v1DBoldDMwLT_2) ) && q_1*q_2 < 0",
                "C":"&& byTightIsolationMVArun2v1DBoldDMwLT_1 && byTightIsolationMVArun2v1DBoldDMwLT_2 && q_1*q_2 > 0",
                "D":"&& ( (byTightIsolationMVArun2v1DBoldDMwLT_1 && byLooseIsolationMVArun2v1DBoldDMwLT_2 && !byTightIsolationMVArun2v1DBoldDMwLT_2) ) && q_1*q_2 > 0",
            }
            vetos = "passesThirdLepVeto && passesTauLepVetos && trg_doubletau"

            datahists = {}
            for reg, isocut in regions.items():
                datahists[reg]= fillHisto(datain[0],vetos + isocut, variable, weights, lumi, "data"+reg, binning, weight = False)

            for sample,name,addcut in mcin:
                if not name in what: continue
                for reg, isocut in regions.items():

                    tmp_MC = fillHisto(sample,vetos + isocut + addcut, variable, weights, lumi, name+reg, binning, weight = True)
                    datahists[reg].Add( tmp_MC, -1 )

            histos["QCD"] = copy.deepcopy(datahists["B"])
            histos["QCD"].Scale(  datahists["C"].Integral()  / float(datahists["D"].Integral() ) )
            histos["QCD"].SetFillColor( getColor( "QCD" ) )
            histos["QCD"].SetLineColor( R.kBlack )  


    # print histos["QCD"].Integral(), "QCD"

#############################################

    data = fillHisto(datain[0],cut+ sign_cut, variable, weights, lumi, "data_obs", binning, weight = asimov )


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

    histos["ratio"]    = copy.deepcopy( ratio )
    histos["stack"]    = copy.deepcopy( stack )
    histos["data"]     = copy.deepcopy( data )
    histos["leg"]      = copy.deepcopy( leg )

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
    if name in ["qqH"]:            return R.TColor.GetColor(204,102,0)
    if name in ["ggH"]:            return R.TColor.GetColor(255,128,0)
    if name in ["W"]:              return R.TColor.GetColor(222,90,106)
    if name in ["VVT","VVJ","VV"]: return R.TColor.GetColor(175,35,80)
    if name in ["ZL","ZJ","ZLJ"]:  return R.TColor.GetColor(100,192,232)
    if name in ["QCD","WSS"]:      return R.TColor.GetColor(250,202,255)
    if name in ["ZTT","DY"]:       return R.TColor.GetColor(248,206,104)
    else: return R.kYellow

def getMergedSamples(channel, version, svfit):

    path = "/data/higgs/data_2016/ntuples_{0}/{1}/ntuples_{2}_merged/".format(version, channel,svfit)
    ext = "_{0}_{1}.root".format(channel,version)

    mc = [
        (path + "BASIS_ntuple_GluGluHToTauTau_M125_powheg_MCSummer16"+ext,"ggH125",""),
        (path + "BASIS_ntuple_VBFHToTauTau_M125_powheg_MCSummer16"+ext,"qqH125",""),
        (path + "BASIS_ntuple_WXJets_merged_MCSummer16"+ext,"W",""),
        (path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"DY",""),
        (path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"ZTT"," && gen_match_2 == 5"),
        (path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"ZL"," && gen_match_2 < 5"),
        (path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"ZJ"," && gen_match_2 == 6"),
        (path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TT",""),
        (path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TTT","&& gen_match_2 == 5"),
        (path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TTJ","&& gen_match_2 != 5"),
        (path + "BASIS_ntuple_VV_MCSummer16"+ext,"VV",""),
        (path + "BASIS_ntuple_VV_MCSummer16"+ext,"VVT","&& gen_match_2 == 5"),
        (path + "BASIS_ntuple_VV_MCSummer16"+ext,"VVJ","&& gen_match_2 != 5"),
        (path + "BASIS_ntuple_EWKZ_merged_MCSummer16"+ext,"EWKZ",""),
    ]
    data = {
        "mt":(path + "BASIS_ntuple_SingleMuon"+ext,"data",""),
        "et":(path + "BASIS_ntuple_SingleElectron"+ext,"data",""),
        "tt":(path + "BASIS_ntuple_Tau"+ext,"data","")
    }  
    return mc, data[channel], False

def getXCheck( check, channel, vs, svfit ):

    path = "/data/higgs/data_2016/ntuples_{version}/{channel}/ntuples_{svfit}_merged/"
    ext = "_{channel}_{version}.root"

    mc = {
        "ggH125": [path + "BASIS_ntuple_GluGluHToTauTau_M125_powheg_MCSummer16"+ext,"ggH125",""],
        "qqH125": [path + "BASIS_ntuple_VBFHToTauTau_M125_powheg_MCSummer16"+ext,"qqH125",""],
        "W":      [path + "BASIS_ntuple_WXJets_merged_MCSummer16"+ext,"W",""],
        "DY":     [path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"DY",""],
        "ZTT":    [path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"ZTT"," && {0}".format( genM("had", channel) ) ],
        "ZL":     [path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"ZL", " && {0}".format( genM("lep", channel) ) ],
        "ZJ":     [path + "BASIS_ntuple_DYXJetsToLL_lowMass_merged_MCSummer16"+ext,"ZJ", " && {0}".format( genM("jet", channel) ) ],
        "TT":     [path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TT",""],
        "TTT":    [path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TTT"," && {0}".format( genM("had", channel) ) ],
        "TTJ":    [path + "BASIS_ntuple_TT_merged_MCSummer16"+ext,"TTJ"," && !{0}".format( genM("had", channel) ) ],
        "VV":     [path + "BASIS_ntuple_VV_MCSummer16"+ext,"VV",""],
        "VVT":    [path + "BASIS_ntuple_VV_MCSummer16"+ext,"VVT"," && {0}".format( genM("had", channel) ) ],
        "VVJ":    [path + "BASIS_ntuple_VV_MCSummer16"+ext,"VVJ"," && !{0}".format( genM("had", channel) ) ],
        "EWKZ":   [path + "BASIS_ntuple_EWKZ_merged_MCSummer16"+ext,"EWKZ",""],
    }
    data = {
        "mt":[path + "BASIS_ntuple_SingleMuon"+ext,"data",""],
        "et":[path + "BASIS_ntuple_SingleElectron"+ext,"data",""],
        "tt":[path + "BASIS_ntuple_Tau"+ext,"data",""]
    }

    if check == "data":
        asimov = True
        old = ( data[channel][0].format(channel = channel, version = vs[0], svfit = svfit), data[channel][1], data[channel][2] )
        new = ( data[channel][0].format(channel = channel, version = vs[1], svfit = svfit), data[channel][1]+"new", data[channel][2] )
    else:
        asimov = True
        old = ( mc[check][0].format(channel = channel, version = vs[0], svfit = svfit), mc[check][1], mc[check][2] )
        new = ( mc[check][0].format(channel = channel, version = vs[1], svfit = svfit), mc[check][1], mc[check][2] )


    return [old], new, asimov

def genM( what, channel ):
    gens = {
        "lep":{
            "mt":"(gen_match_2 < 5)",
            "et":"(gen_match_2 < 5)",
            "tt":"( !( gen_match_1 == 5 && gen_match_2 == 5 ) && gen_match_1 < 6 && gen_match_2 < 6  )"
        },
        "had":{
            "mt":"(gen_match_2 == 5)",
            "et":"(gen_match_2 == 5)",
            "tt":"( gen_match_1 == 5 && gen_match_2 == 5 )"
        },
        "jet":{
            "mt":"(gen_match_2 == 6)",
            "et":"(gen_match_2 == 6)",
            "tt":"( gen_match_1 == 6 || gen_match_2 == 6 )"
        }
    }
    return gens[what][channel]


if __name__ == '__main__':

    main()


