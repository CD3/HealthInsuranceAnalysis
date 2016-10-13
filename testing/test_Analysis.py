#! env python

from HIA.Analysis import *

def test_units():

  assert Q_(100,'dollar').to('').magnitude == 100
  assert Q_(100,'dollar').magnitude == 100
  assert Q_(100,'dollar').to('cent').magnitude == 10000


def test_DeductiblePortion():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar

  a = Analysis( p )

  assert a.DeductiblePortion(0) == 0
  assert a.DeductiblePortion(100) == 100
  assert a.DeductiblePortion(1000) == 1000
  assert a.DeductiblePortion(4999) == 4999
  assert a.DeductiblePortion(5001) == 5000
  assert a.DeductiblePortion(10000) == 5000


def test_CoinsurancePortion():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar

  a = Analysis( p )

  assert a.CoinsurancePortion(0) == 0
  assert a.CoinsurancePortion(100) == 0
  assert a.CoinsurancePortion(1000) == 0
  assert a.CoinsurancePortion(10000) == 1000
  assert a.CoinsurancePortion(25000) == 4000
  assert a.CoinsurancePortion(30000) == 5000
  assert a.CoinsurancePortion(40000) == 5000
  assert a.CoinsurancePortion(100000) == 5000


def test_Responsibility():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar

  a = Analysis( p )
  assert a.Responsibility(0) == 0
  assert a.Responsibility(100) == 100
  assert a.Responsibility(1000) == 1000
  assert a.Responsibility(10000) == 6000
  assert a.Responsibility(25000) == 9000
  assert a.Responsibility(30000) == 10000
  assert a.Responsibility(56000) == 10000
  assert a.Responsibility(100000) == 10000


def test_HSAPayment():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  p.HSA_initial = 0*u.dollar
  p.HSA_employer_contribution = 1000*u.dollar/u.year
  p.HSA_employee_contribution = 25*u.dollar/u.semimonth
  
  assert p.HSA_employee_contribution.to('dollar/year').magnitude == 600
  assert p.HSA_employee_contribution*u.year == 600

  a = Analysis( p )

  assert a.HSAPayment(0) == 0
  assert a.HSAPayment(100) == 100
  assert a.HSAPayment(1000) == 1000
  assert a.HSAPayment(2000) == 1600



  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  
  assert p.HSA_employee_contribution is None
  assert p.HSA_employee_contribution is None

  a = Analysis( p )

  assert a.HSAPayment(0) == 0
  assert a.HSAPayment(100) == 0
  assert a.HSAPayment(1000) == 0
  assert a.HSAPayment(2000) == 0

def test_OutOfPocketPayment():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  p.HSA_initial = 0*u.dollar
  p.HSA_employer_contribution = 1000*u.dollar/u.year
  p.HSA_employee_contribution = 25*u.dollar/u.semimonth
  
  assert p.HSA_employee_contribution.to('dollar/year').magnitude == 600
  assert p.HSA_employee_contribution*u.year == 600

  a = Analysis( p )

  assert a.OutOfPocketPayment(0) == 0
  assert a.OutOfPocketPayment(100) == 0
  assert a.OutOfPocketPayment(1000) == 0
  assert a.OutOfPocketPayment(2000) == 400


def test_InsurancePayment():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  p.HSA_initial = 0*u.dollar
  p.HSA_employer_contribution = 1000*u.dollar/u.year
  p.HSA_employee_contribution = 25*u.dollar/u.semimonth
  
  a = Analysis( p )

  assert a.InsurancePayment(0) == 0
  assert a.InsurancePayment(100) == 0
  assert a.InsurancePayment(1000) == 0
  assert a.InsurancePayment(2000) == 0
  assert a.InsurancePayment(5000) == 0
  assert a.InsurancePayment(6000) == 800
  assert a.InsurancePayment(10000) == 4000
  assert a.InsurancePayment(25000) == 16000
  assert a.InsurancePayment(30000) == 20000
  assert a.InsurancePayment(35000) == 25000
  assert a.InsurancePayment(100000) == 90000


def test_Insurance100PercentPayExpense():
  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 50*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  
  a = Analysis( p )

  assert a.Insurance100PercentPayExpense() == 15000


def test_TotalCost():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  p.HSA_initial = 0*u.dollar
  p.premium = 1000*u.dollar/u.month

  assert (p.premium * u.year).to('dollar') == 12000
  
  a = Analysis( p )

  assert a.TotalCost(0) == 12000
  assert a.TotalCost(100000) == 12000+10000


  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  p.HSA_initial = 0*u.dollar
  p.HSA_employee_contribution = 25*u.dollar/u.semimonth
  p.premium = 1000*u.dollar/u.month

  assert (p.premium * u.year).to('dollar') == 12000
  assert (p.HSA_employee_contribution*u.year).to('dollar') == 600
  
  a = Analysis( p )

  assert a.TotalCost(0) == 12600
  assert a.TotalCost(100000) == 12000+10000 # the HSA contribution will add to cost but reduce responsibility


def test_Analysis():

  p = InsurancePlan()
  p.deductible = 5000*u.dollar
  p.coinsurance = 20*u.percent
  p.out_of_pocket_max = 10000*u.dollar
  p.HSA_initial = 0*u.dollar
  p.HSA_employer_contribution = 1000*u.dollar/u.year
  p.HSA_employee_contribution = 25*u.dollar/u.semimonth
  p.premium = 100*u.dollar/u.semimonth

  assert p.premium*u.year == 2400

  a = Analysis(p)

  report = a.run(0)
  assert report['out of pocket payment'] == 0

  report = a.run(2000)
  assert report['out of pocket payment'] == 400

  report = a.run(100000)
  assert report['out of pocket payment'] == 10000-1600
  assert report['insurance payment'] == 90000
  assert report['HSA payment'] + report['out of pocket payment'] + report['insurance payment'] == 100000


def test_utils():

  assert make_Q_( 100 ) == 100*u.dollar
  assert make_Q_( 100*u.cent ) == 100*u.cent
  assert make_Q_( '100' ) == 100*u.dollar
  assert make_Q_( '100 cent' ) == 100*u.cent

def test_InsurancePlan_config():

  text = '''
  deductible  : 5000 dollar
  coinsurance : 20 %
  out of pocket max : 10000
  test : 1
  nested :
    one : 1
    nested :
      two : 2
      test : 1
      x : 1
  '''

  p = InsurancePlan()

  assert p.deductible is None
  assert p.coinsurance is None
  assert p.out_of_pocket_max is None

  p.load(text)

  assert p.deductible == 5000
  assert p.coinsurance == 0.2
  assert p.out_of_pocket_max == 10000

def test_Analysis_config():

  text = '''
  plan :
    deductible  : 5000 dollar
    coinsurance : 20 %
    out of pocket max : 10000
    premium : 100 dollar/semimonth
  '''

  a = Analysis()
  a.load( text )

  assert a.plan.deductible == 5000
  assert a.plan.coinsurance == 0.2
  assert a.plan.out_of_pocket_max == 10000
  assert (a.plan.premium * u.year).to('dollar') == 2400


