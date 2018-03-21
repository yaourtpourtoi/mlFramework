import ROOT as R

def calc(varname):
    if varname == "dijetpt":  return calcDiJetPt
    if varname == "dijetphi": return calcDiJetPhi
    if varname == "pt_vis":    return calcPtVis

def calcDiJetPt(row):
    if row["jpt_1"] < 0 or row["jpt_2"] < 0: return -10.
    jet1 = R.TLorentzVector()
    jet2 = R.TLorentzVector()

    jet1.SetPtEtaPhiM( row["jpt_1"], row["jeta_1"], row["jphi_1"], row["jm_1"] )
    jet2.SetPtEtaPhiM( row["jpt_2"], row["jeta_2"], row["jphi_2"], row["jm_2"] )

    dijet = jet1 + jet2
    return dijet.Pt()

def calcDiJetPhi(row):
    if row["jpt_1"] < 0 or row["jpt_2"] < 0: return -10.
    jet1 = R.TLorentzVector()
    jet2 = R.TLorentzVector()

    jet1.SetPtEtaPhiM( row["jpt_1"], row["jeta_1"], row["jphi_1"], row["jm_1"] )
    jet2.SetPtEtaPhiM( row["jpt_2"], row["jeta_2"], row["jphi_2"], row["jm_2"] )

    dijet = jet1 + jet2
    return dijet.Phi()

def calcPtVis(row):

    leg1 = R.TLorentzVector()
    leg2 = R.TLorentzVector()

    leg1.SetPtEtaPhiM( row["pt_1"], row["eta_1"], row["phi_1"], row["m_1"] )
    leg2.SetPtEtaPhiM( row["pt_2"], row["eta_2"], row["phi_2"], row["m_2"] )

    vis = leg1 + leg2
    return vis.Pt()