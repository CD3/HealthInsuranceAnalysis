#! env python

import os, sys, re, pint

ureg = pint.UnitRegistry()
u = ureg
Q_ = ureg.Quantity

ureg.define('semimonth = year/24')
ureg.define('percent = 0.01*radian = cent')
ureg.define('dollar = radian')

class InsurancePlan(object):
  def __init__(self):
    # benefits
    self.deductible = None
    self.coinsurance = None
    self.out_of_pocket_max = None
    self.HSA_initial = None
    self.HSA_employer_contribution = None

    # costs
    self.HSA_employee_contribution = None
    self.premium = None

class Visit(object):
  def __init__(self):
    self.charge = None
    self.type = None

class MedicalExpenses(object):
  def __init__(self):
    self.visits = list()
    self.charges = None

class Analysis(object):

  def __init__(self,plan = None):
    self.plan = plan

  def _norm_args(self,expenses,plan):
    if plan is None:
      plan = self.plan
    if not isinstance( expenses, Q_ ):
      expenses = Q_(expenses,'dollar')
    return expenses,plan

  def run(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )

    report = dict()

    report['expenses']               = expenses
    report['deductible portion']    = self.DeductiblePortion(expenses,plan)
    report['coinsurance portion']   = self.CoinsurancePortion(expenses,plan)
    report['responsibility']        = self.Responsibility(expenses,plan)
    report['HSA payment']           = self.HSAPayment(expenses,plan)
    report['out of pocket payment'] = self.OutOfPocketPayment(expenses,plan)
    report['insurance payment']     = self.InsurancePayment(expenses,plan)

    return report

  def DeductiblePortion(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    C = expenses
    D = plan.deductible
    return min( C, D )

  def CoinsurancePortion(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    C = expenses
    D = plan.deductible
    Cr = plan.coinsurance.to('').magnitude
    OOPM = plan.out_of_pocket_max

    DP = self.DeductiblePortion(expenses,plan)
    CP = (C - DP)*Cr
    CPMax = OOPM-D
    return min( CP, CPMax)

  def Responsibility(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    return self.DeductiblePortion(expenses,plan) + self.CoinsurancePortion(expenses,plan)

  def HSAPayment(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    Res = self.Responsibility( expenses,plan )
    HSA_0 = plan.HSA_initial if plan.HSA_initial else 0*u.dollar
    HSA_1 = plan.HSA_employer_contribution if plan.HSA_employer_contribution else 0*u.dollar/u.year
    HSA_2 = plan.HSA_employee_contribution if plan.HSA_employee_contribution else 0*u.dollar/u.year
    HSA_Total = HSA_0 + ((HSA_1+HSA_2)*ureg.year).to('').magnitude

    return min( Res, HSA_Total )

  def OutOfPocketPayment(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    return self.Responsibility(expenses,plan) - self.HSAPayment(expenses,plan)

  def InsurancePayment(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    return expenses - self.Responsibility(expenses,plan)

  def TotalCost(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    return self.OutOfPocketPayment(expenses,plan) + (plan.premium*u.year).to('dollar')






