import root_pandas as rp
import ROOT as R
import root_numpy as rn
import copy
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

def plot( histos, canvas = "semi", outfile = "", descriptions = {} ):

    data = histos.pop("data",None)
    yields = [ ( h.Integral(), name ) for name,h in histos.items() ]
    yields.sort()
    what = [ y[1] for y in yields ]

    ratio = copy.deepcopy(  histos[ what[0] ] )
    applyHistStyle( histos[ what[0] ] , what[0] )

    stack = R.THStack("stack", "")
    stack.Add( copy.deepcopy( histos[ what[0] ] ) )
    
    if canvas == "semi":                      leg = R.TLegend(0.82, 0.03, 0.98, 0.92)
    if canvas == "linear" or canvas == "log": leg = R.TLegend(0.82, 0.4, 0.98, 0.92)

    leg.AddEntry( histos[ what[0] ], what[0] )

    for h in what[1:]:
        applyHistStyle( histos[h] , h )
        leg.AddEntry( histos[h], h )
        stack.Add( copy.deepcopy( histos[h] ) )
        ratio.Add( histos[h] )

    if not data:
        data = copy.deepcopy( ratio )

    ratio.Divide( data )

    applyHistStyle(data, "")
    applyHistStyle(ratio, "")

    maxVal = max( stack.GetMaximum(), data.GetMaximum() ) * 1.2
    dummy_up    = copy.deepcopy( data )
    dummy_up.Reset()
    dummy_up.SetTitle("")

    dummy_down  = copy.deepcopy( data )
    dummy_down.Reset()
    dummy_down.SetTitle("")
    dummy_down.GetYaxis().SetRangeUser( 0.1 , maxVal/ 40 )
    dummy_down.GetXaxis().SetLabelSize(0)

    dummy_ratio = copy.deepcopy( ratio )
    dummy_ratio.Reset()
    dummy_ratio.SetTitle("")
    dummy_ratio.GetYaxis().SetRangeUser( 0.5 , 1.5 )
    dummy_ratio.GetYaxis().SetNdivisions(6)
    dummy_ratio.GetXaxis().SetTitleSize(0.12)
    dummy_ratio.GetXaxis().SetTitleOffset(1)
    dummy_ratio.GetXaxis().SetTitle( descriptions.get( "xaxis", "some quantity" ) )

    cms1 = R.TLatex( 0.1, 0.93, "CMS" )
    cms2 = R.TLatex( 0.155, 0.93, descriptions.get( "plottype", "ProjectWork" ) )

    ch = descriptions.get( "channel", "  " )
    lumi = descriptions.get( "lumi", "xx.y" )
    som = descriptions.get( "SoM", "13" )
    l = r"{0}   {1} ".format(ch, lumi)
    r = " ({0} TeV)".format(som)
    righttop = R.TLatex( 0.60, 0.932, l+r"fb_{}^{-1}"+r)

    cms1.SetNDC();
    cms2.SetNDC();
    righttop.SetNDC();
    if canvas == "semi":
        cms1.SetTextSize(0.055);            
        cms2.SetTextFont(12)
        cms2.SetTextSize(0.055);
        righttop.SetTextSize(0.05);

    if canvas == "linear" or canvas == "log":
        cms1.SetTextSize(0.04);            
        cms2.SetTextFont(12)
        cms2.SetTextSize(0.04);
        righttop.SetTextSize(0.035);


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
        R.gPad.RedrawAxis()
        cv.cd(3)
        dummy_ratio.Draw()
        ratio.Draw("same e1")

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
    
    if not outfile:
        outfile = "{0}_canvas.png".format(canvas)

    cv.cd(1)
    cms1.Draw()
    cms2.Draw()
    righttop.Draw()

    cv.SaveAs( outfile )






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
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetRightMargin(0.2)

    cv.cd(2)
    R.gPad.SetTopMargin(0.05)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetBottomMargin(0.05)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetLogy()

    # Set pad margins 2
    cv.cd(3)
    R.gPad.SetTopMargin(0.03)
    R.gPad.SetBottomMargin(0.3)
    R.gPad.SetLeftMargin(0.1)
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
    R.gPad.SetBottomMargin(0.025)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetRightMargin(0.2)

    cv.cd(2)
    R.gPad.SetTopMargin(0.025)
    R.gPad.SetBottomMargin(0.3)
    R.gPad.SetLeftMargin(0.1)
    R.gPad.SetRightMargin(0.2)
    R.gPad.SetGridy()
    # tmpRatio.Draw()

    cv.cd(1)
    return cv

def applyHistStyle(hist, name):

    hist.GetXaxis().SetLabelFont(63)
    hist.GetXaxis().SetLabelSize(14)
    hist.GetYaxis().SetLabelFont(63)
    hist.GetYaxis().SetLabelSize(14)
    hist.SetFillColor( getColor( name ) )
    hist.SetLineColor( R.kBlack )

def getColor(name):

    if name in ["TT","TTT","TTJ"]: return R.TColor.GetColor(155,152,204)
    if name in ["sig"]:            return R.kRed
    if name in ["bkg"]:            return R.kBlue
    if name in ["qqH"]:            return R.TColor.GetColor(204,102,0)
    if name in ["ggH"]:            return R.TColor.GetColor(255,128,0)
    if name in ["W"]:              return R.TColor.GetColor(222,90,106)
    if name in ["VV","VVJ","VVT"]: return R.TColor.GetColor(175,35,80)
    if name in ["ZL","ZJ","ZLJ"]:  return R.TColor.GetColor(100,192,232)
    if name in ["QCD","WSS"]:      return R.TColor.GetColor(250,202,255)
    if name in ["ZTT","DY","real"]:       return R.TColor.GetColor(248,206,104)
    if name in ["jetFakes"]:             return R.TColor.GetColor(192,232,100)
    else: return R.kYellow

if __name__ == '__main__':
    main()