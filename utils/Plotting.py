import root_pandas as rp
import ROOT as R
import root_numpy as rn
import copy
import os
from array import array
R.gROOT.SetBatch(True)
R.gStyle.SetOptStat(0)

def main():

    histos = { "DY":R.TH1D("a","a",100,0,10),
               "QCD":R.TH1D("b","b",100,0,10),
               "data":R.TH1D("data","data",100,0,10), }




    for i in xrange(1,100):
        histos["DY"].SetBinContent(i,i*0.1)
        histos["QCD"].SetBinContent(i,i*10)
        histos["data"].SetBinContent(i,i*0.1 + i*10)


    plot(histos,"log")

def plot( histos, signal=[], canvas = "semi", outfile = "", descriptions = {} ):



    data = histos.pop("data",None)
    signal_hists = []

    for i,s in enumerate(signal):
        tmp = histos.pop(s, None)
        if tmp:
            applySignalHistStyle(tmp, s,3)
            signal_hists.append( tmp )
            
    yields = [ ( h.Integral(), name ) for name,h in histos.items() ]
    yields.sort()
    what = [ y[1] for y in yields ]

    cumul = copy.deepcopy(  histos[ what[0] ] )
    applyHistStyle( histos[ what[0] ] , what[0] )

    stack = R.THStack("stack", "")
    stack.Add( copy.deepcopy( histos[ what[0] ] ) )
    
    for h in what[1:]:
        applyHistStyle( histos[h] , h )
        stack.Add( copy.deepcopy( histos[h] ) )
        cumul.Add( histos[h] )

    if not data:
        data = copy.deepcopy( cumul )

    ratio = copy.deepcopy( data )
    ratio.Divide( cumul )

    if signal:
        signal_ratio = copy.deepcopy( cumul )
        for s in signal_hists:
            signal_ratio.Add( copy.deepcopy( s ) )
        signal_ratio.Divide(cumul)
        applySignalHistStyle(signal_ratio, "sig", 2 )


    applySignalHistStyle(data, "data")
    applyHistStyle(ratio, "")

    if canvas == "semi":                      
        leg = R.TLegend(0.82, 0.03, 0.98, 0.92)
        leg.SetTextSize(0.05)
    if canvas == "linear" or canvas == "log":
        leg = R.TLegend(0.82, 0.29, 0.98, 0.92)
        leg.SetTextSize(0.035)
    
    leg.AddEntry( data, "data obs." )

    for n in reversed(what):
        leg.AddEntry( histos[n], getFancyName(n) )
    for s in signal_hists:
        leg.AddEntry( s, getFancyName( s.GetName() ) )


    maxVal = max( stack.GetMaximum(), data.GetMaximum() ) * 1.2
    dummy_up    = copy.deepcopy( data )
    dummy_up.Reset()
    dummy_up.SetTitle("")

    dummy_down  = copy.deepcopy( data )
    dummy_down.Reset()
    dummy_down.SetTitle("")
    dummy_down.GetYaxis().SetRangeUser( 0.1 , maxVal/ 40 )
    dummy_down.GetXaxis().SetLabelSize(0)
    dummy_down.GetXaxis().SetTitle("")

    dummy_ratio = copy.deepcopy( ratio )
    dummy_ratio.Reset()
    dummy_ratio.SetTitle("")
    dummy_ratio.GetYaxis().SetRangeUser( 0.5 , 1.5 )
    dummy_ratio.GetYaxis().SetNdivisions(6)
    dummy_ratio.GetXaxis().SetTitleSize(0.12)
    dummy_ratio.GetXaxis().SetTitleOffset(1)
    dummy_ratio.GetXaxis().SetTitle( descriptions.get( "xaxis", "some quantity" ) )

    cms1 = R.TLatex( 0.08, 0.93, "CMS" )
    cms2 = R.TLatex( 0.135, 0.93, descriptions.get( "plottype", "ProjectWork" ) )

    chtex = {"et":r"e#tau","mt":r"#mu#tau","tt":r"#tau#tau","em":r"e#mu"}
    ch = descriptions.get( "channel", "  " )
    ch = chtex.get(ch,ch)
    channel = R.TLatex( 0.60, 0.932, ch )

    lumi = descriptions.get( "lumi", "xx.y" )
    som = descriptions.get( "SoM", "13" )
    l = lumi + r" fb^{-1}"
    r = " ({0} TeV)".format(som)
    righttop = R.TLatex( 0.635, 0.932, l+r)



    cms1.SetNDC();
    cms2.SetNDC();
    righttop.SetNDC();
    channel.SetNDC();

    if canvas == "semi":
        cms1.SetTextSize(0.055)            
        cms2.SetTextFont(12)
        cms2.SetTextSize(0.055)
        righttop.SetTextSize(0.05)
        channel.SetTextSize(0.06)

        semi_info = R.TLatex( 0.83, 0.2, "log-scale")
        semi_info.SetTextAngle(90)
        semi_info.SetNDC();
        semi_info.SetTextSize(0.15)
        semi_info.SetTextColor(  R.TColor.GetColor(125,125,125) )

    if canvas == "linear" or canvas == "log":
        cms1.SetTextSize(0.04);            
        cms2.SetTextFont(12)
        cms2.SetTextSize(0.04);
        righttop.SetTextSize(0.035);
        channel.SetTextSize(0.045)


    if canvas == "semi":
        dummy_up.GetYaxis().SetRangeUser( maxVal/ 40 , maxVal )

        cv= createRatioSemiLogCanvas("cv" )

        cv.cd(1)
        dummy_up.Draw()
        stack.Draw("same hist")
        data.Draw("same e1")
        leg.Draw()
        R.gPad.RedrawAxis()
        cv.cd(2)
        dummy_down.Draw()
        stack.Draw("same hist")
        data.Draw("same e1")
        for s in signal_hists:
            s.Draw("same hist")

        semi_info.Draw()

        R.gPad.RedrawAxis()
        cv.cd(3)
        dummy_ratio.Draw()
        ratio.Draw("same e1")
        if signal:
            signal_ratio.Draw("same hist")

    if canvas == "linear" or canvas == "log":

        if canvas == "linear": dummy_up.GetYaxis().SetRangeUser( 0 , maxVal )
        if canvas == "log": dummy_up.GetYaxis().SetRangeUser( 0.1 , maxVal )
        dummy_up.GetXaxis().SetLabelSize(0)

        cv= createRatioCanvas("cv" )

        cv.cd(1)
        if canvas == "log": R.gPad.SetLogy()

        dummy_up.Draw()
        stack.Draw("same hist")
        data.Draw("same e1")
        leg.Draw()
        cv.cd(2)
        dummy_ratio.Draw()
        ratio.Draw("same e1")
        if signal:
            signal_ratio.Draw("same hist")
    
    if not outfile:
        outfile = "{0}_canvas.png".format(canvas)

    cv.cd(1)
    cms1.Draw()
    cms2.Draw()
    channel.Draw()
    righttop.Draw()

    cv.SaveAs( "/".join([os.getcwd(),outfile]) )






def createRatioSemiLogCanvas(name):

    cv = R.TCanvas(name, name, 10, 10, 700, 600)

    # this is the tricky part...
    # Divide with correct margins
    cv.Divide(1, 3, 0.0, 0.0)

    # Set Pad sizes
    cv.GetPad(1).SetPad(0.0, 0.45, 1., 1.0)
    cv.GetPad(2).SetPad(0.0, 0.25, 1., 0.465)
    cv.GetPad(3).SetPad(0.0, 0.00, 1., 0.25)

    cv.GetPad(1).SetFillStyle(4000)
    cv.GetPad(2).SetFillStyle(4000)
    cv.GetPad(3).SetFillStyle(4000)

    # Set pad margins 1
    cv.cd(1)
    R.gPad.SetTopMargin(0.08)
    R.gPad.SetBottomMargin(0)
    R.gPad.SetLeftMargin(0.08)
    R.gPad.SetRightMargin(0.2)

    cv.cd(2)
    R.gPad.SetTopMargin(0.05)
    R.gPad.SetLeftMargin(0.08)
    R.gPad.SetBottomMargin(0.05)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetLogy()

    # Set pad margins 2
    cv.cd(3)
    R.gPad.SetTopMargin(0.03)
    R.gPad.SetBottomMargin(0.3)
    R.gPad.SetLeftMargin(0.08)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetGridy()

    cv.cd(1)
    return cv

def createRatioCanvas(name):

    cv = R.TCanvas(name, name, 10, 10, 700, 600)

    # this is the tricky part...
    # Divide with correct margins
    cv.Divide(1, 2, 0.0, 0.0)

    # Set Pad sizes
    cv.GetPad(1).SetPad(0.0, 0.25, 1., 1.0)
    cv.GetPad(2).SetPad(0.0, 0.00, 1., 0.25)

    cv.GetPad(1).SetFillStyle(4000)
    cv.GetPad(2).SetFillStyle(4000)

    # Set pad margins 1
    cv.cd(1)
    R.gPad.SetTopMargin(0.08)
    R.gPad.SetBottomMargin(0.01)
    R.gPad.SetLeftMargin(0.08)
    R.gPad.SetRightMargin(0.2)

    cv.cd(2)
    R.gPad.SetTopMargin(0.03)
    R.gPad.SetBottomMargin(0.3)
    R.gPad.SetLeftMargin(0.08)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetGridy()

    cv.cd(1)
    return cv

def applyHistStyle(hist, name):

    hist.GetXaxis().SetLabelFont(63)
    hist.GetXaxis().SetLabelSize(14)
    hist.GetYaxis().SetLabelFont(63)
    hist.GetYaxis().SetLabelSize(14)
    hist.SetFillColor( getColor( name ) )
    hist.SetLineColor( R.kBlack )

def applySignalHistStyle(hist, name, width = 1):

    hist.GetXaxis().SetLabelFont(63)
    hist.GetXaxis().SetLabelSize(14)
    hist.GetYaxis().SetLabelFont(63)
    hist.GetYaxis().SetLabelSize(14)
    hist.SetFillColor( 0 )
    hist.SetLineWidth( width )
    hist.SetLineColor( getColor( name ) )


def getFancyName(name):
    if name == "ZL":         return r"Z (l#rightarrow#tau)"
    if name == "ZJ":         return r"Z (jet#rightarrow#tau)"
    if name == "ZTT":        return r"Z #rightarrow #tau#tau"
    if name == "TTT":        return r"t#bar{t} (#tau#rightarrow#tau)"
    if name == "TTJ":        return r"t#bar{t} (jet#rightarrow#tau)"
    if name == "VVT":        return r"VV (#tau#rightarrow#tau)"
    if name == "VVJ":        return r"VV (jet#rightarrow#tau)"
    if name == "W":          return r"W + jet"
    if name == "QCD":        return r"MultiJet"
    if name == "jetFakes":   return r"jet #rightarrow #tau_{h}"
    if name == "EWKZ":       return r"EWKZ"
    if name in ["qqH","qqH125"]:    return "VBF"
    if name in ["ggH","ggH125"]:    return "ggF"

    return name



def getColor(name):

    if name in ["TT","TTT","TTJ"]:  return R.TColor.GetColor(155,152,204)
    if name in ["sig"]:             return R.kRed
    if name in ["bkg"]:             return R.kBlue
    if name in ["qqH","qqH125"]:    return R.TColor.GetColor(0,100,0)
    if name in ["ggH","ggH125"]:    return R.TColor.GetColor(0,0,100)
    if name in ["W"]:               return R.TColor.GetColor(222,90,106)
    if name in ["VV","VVJ","VVT"]:  return R.TColor.GetColor(175,35,80)
    if name in ["ZL","ZJ","ZLJ"]:   return R.TColor.GetColor(100,192,232)
    if name in ["EWKZ"]:            return R.TColor.GetColor(8,247,183)
    if name in ["QCD","WSS"]:       return R.TColor.GetColor(250,202,255)
    if name in ["ZTT","DY","real"]: return R.TColor.GetColor(248,206,104)
    if name in ["jetFakes"]:        return R.TColor.GetColor(192,232,100)
    if name in ["data"]:            return R.TColor.GetColor(0,0,0)
    else: return R.kYellow

if __name__ == '__main__':
    main()
