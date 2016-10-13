#! env python

import os, sys, re, pint, yaml, dpath

ureg = pint.UnitRegistry()
u = ureg
Q_ = ureg.Quantity

ureg.define('semimonth = year/24')
ureg.define('percent = 0.01*radian = cent')
ureg.define('dollar = radian')

string = (str,unicode)

def make_Q_(s, default_unit = 'dollar' ):
  if s is None:
    return s

  if isinstance(s,Q_):
    return s

  try:
    q = Q_(s)
    if q.units == u.dimensionless:
      q.ito('dollar')
    return q
  except:
    return -1

def norm_config( d ):
  '''Normalize a configuration dict. This allows support for config key aliases.'''
  mappings = { '^test' : "NORMALIZED"
             , '^oopm' : 'out of pocket max'
             , '^ded.*'  : 'deductible'
             }

  dd = dict()
  for k,v in dpath.util.search( d, "**", yielded=True, afilter = lambda x: True, separator='/' ):
    if isinstance( v, string ):
      v = re.sub( '%\s*$', ' percent', v )

    k = k.lower()
    root,base = os.path.split(k)
    for pat,rep in mappings.items():
      if re.search( pat, base ):
        base = rep
    kk = os.path.join( root,base )
    dpath.util.new( dd, kk, v )

  return dd

class InsurancePlan(object):
  def __init__(self,d=dict()):
    self.load(d)

  def load( self, d ):
    if isinstance( d, string ):
      return self.load( yaml.load(d) )

    d = norm_config(d)

    self.deductible                = make_Q_( d.get('deductible', None) )
    self.coinsurance               = make_Q_( d.get('coinsurance', None) )
    self.out_of_pocket_max         = make_Q_( d.get('out of pocket max', None ) )
    self.HSA_initial               = make_Q_( d.get('hsa initial', None ) )
    self.HSA_employer_contribution = make_Q_( d.get('hsa employer contribution', None) )

    self.HSA_employee_contribution = make_Q_( d.get('hsa employee contribution', None) )
    self.premium                   = make_Q_( d.get('premium', None ) )

    # print
    # print d
    # print self.__dict__

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

  def load(self, d):

    if isinstance( d, string ):
      return self.load( yaml.load(d) )

    d = norm_config(d)

    self.plan = InsurancePlan(d.get('plan',{}))


    pass
  def run(self, expenses, plan = None, stripunits = False):
    expenses,plan = self._norm_args( expenses,plan )

    report = dict()

    report['expenses']              = expenses.to('dollar').magnitude
    report['deductible portion']    = self.DeductiblePortion(expenses,plan).to('dollar').magnitude
    report['coinsurance portion']   = self.CoinsurancePortion(expenses,plan).to('dollar').magnitude
    report['responsibility']        = self.Responsibility(expenses,plan).to('dollar').magnitude
    report['HSA payment']           = self.HSAPayment(expenses,plan).to('dollar').magnitude
    report['out of pocket payment'] = self.OutOfPocketPayment(expenses,plan).to('dollar').magnitude
    report['insurance payment']     = self.InsurancePayment(expenses,plan).to('dollar').magnitude
    report['premium']               = self.Premium(plan).to('dollar').magnitude
    report['HSA contributions']     = self.HSAEmployeeContribution(plan).to('dollar').magnitude
    report['total cost']            = self.TotalCost(expenses).to('dollar').magnitude

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

  def Insurance100PercentPayExpense(self,plan = None):
    '''Calculate the point at which insurance will start to pay 100% of additional expenses.'''
    trash,plan = self._norm_args(0,plan)
    D = plan.deductible
    C = plan.coinsurance
    OOPM = plan.out_of_pocket_max

    CMax  = OOPM - D  # coinsurance max
    CExpense = CMax/C # expensed dollars that give the coinsurance max

    return D + CExpense



  def HSAEmployeeContribution(self, plan = None):
    trash,plan = self._norm_args(0,plan)
    return (plan.HSA_employee_contribution*u.year).to('dollar') if plan.HSA_employee_contribution else 0*u.dollar

  def Premium(self, plan = None):
    trash,plan = self._norm_args(0,plan)
    return (self.plan.premium*u.year).to('dollar')

  def TotalCost(self, expenses, plan = None):
    expenses,plan = self._norm_args( expenses,plan )
    HSA_cont = (plan.HSA_employee_contribution*u.year).to('dollar') if plan.HSA_employee_contribution else 0*u.dollar
    return self.OutOfPocketPayment(expenses,plan) + (plan.premium*u.year).to('dollar') + HSA_cont






