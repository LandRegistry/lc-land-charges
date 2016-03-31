

require 'date'
require 'net/http'
require 'json'
require_relative '../../../acceptance-tests/features/support/rest_api'

$B2B_API_URI = ENV['PUBLIC_API_URL'] || 'http://localhost:5001'
$B2B_PROCESSOR_URI = ENV['AUTOMATIC_PROCESS_URL'] || 'http://localhost:5002'
$BANKRUPTCY_REGISTRATION_URI = ENV['LAND_CHARGES_URL'] || 'http://localhost:5004'
$LAND_CHARGES_URI = ENV['LAND_CHARGES_URL'] || 'http://localhost:5004'
$CASEWORK_API_URI = ENV['CASEWORK_API_URL'] || 'http://localhost:5006'
$LEGACY_DB_URI = ENV['LEGACY_ADAPTER_URL'] || 'http://localhost:5007'
$FRONTEND_URI = ENV['CASEWORK_FRONTEND_URL'] || 'http://localhost:5010'

def register(data)
    lc_api = RestAPI.new($LAND_CHARGES_URI)
    reg1 = lc_api.post('/registrations?dev_date=2016-01-01', data)

    puts reg1
    date = reg1['new_registrations'][0]['date']
    number = reg1['new_registrations'][0]['number']
    {
        "date" => date,
        "number" => number
    }
end

`clear-data`
puts `ruby ../../../acceptance-tests/data/lc-lookups.rb`




#"uri": "2016-02-28/1004",

pab_1 = '{"applicant": {"name": "Waste of space", "address_type": "NA", "address": "2 New Street, My Town", "key_number": "1234567", "reference": " "}, "parties":[{"names": [{"type": "Private Individual", "private": {"forenames": ["Mister"], "surname": "Bankrupt" }}], "trading_name": " ", "addresses": [{"county": "Devon", "address_lines": ["2 new street", "Plymouth"], "postcode": "PL3 3PL", "type": "Residence", "address_string": "2 new street Plymouth Devon PL3 3PL"}], "occupation": "", "type": "Debtor", "residence_withheld": false, "case_reference": "Devon County Court 123 of 2016", "legal_body": "Plymouth County Court", "legal_body_ref_no": "123 of 2016", "legal_body_ref_year": 2016, "counties": ["Devon", "Dorset"]}], "class_of_charge": "PAB"}'

wob_1 = '{"parties": [{"type": "Debtor", "legal_body_ref_no": "123 of 2016", "trading_name": " ", "occupation": "Unemployed", "case_reference": "Devon County Court 123 of 2016", "names": [{"type": "Private Individual", "private": {"surname": "Bankrupt", "forenames": ["Mister"]}}], "legal_body": "Devon County Court", "addresses": [{"county": "Devon", "type": "Residence", "postcode": "OT1 1AA", "address_lines": ["1 Other Road", "Otherton"], "address_string": "1 Other Road Otherton Devon OT1 1AA"}], "residence_withheld": false}], "class_of_charge": "WOB", "applicant": {"key_number": "1234567", "address_type": "NA", "address": "49 Camille Circles Port Eulah PP39 6BY", "reference": " ", "name": "S & H Legal Group"}}'

amendment = '"parties": [{"residence_withheld": false, "trading_name": " ", "legal_body_ref_no": "123 of 2016", "legal_body": "Devon County Court", "type": "Debtor", "case_reference": "Devon County Court 123 of 2016", "addresses": [{"type": "Residence", "postcode": "Blah", "county": "Blah", "address_lines": ["1 Other Road", "Blah"], "address_string": "1 Other Road Blah Blah Blah"}], "names": [{"type": "Private Individual", "private": {"forenames": ["Mister"], "surname": "Bankrupt"}}], "occupation": "Truck Driver"}], "class_of_charge": "WOB", "update_registration": {"type": "Amendment"}, "applicant": {"key_number": "1234567", "name": "S & H Legal Group", "address_type": "NA", "address": "49 Camille Circles Port Eulah PP39 6BY", "reference": " "}}'

amendment_add_name = '"parties": [{"residence_withheld": false, "trading_name": " ", "legal_body_ref_no": "123 of 2016", "legal_body": "Devon County Court", "type": "Debtor", "case_reference": "Devon County Court 123 of 2016", "addresses": [{"type": "Residence", "postcode": "Blah", "county": "Blah", "address_lines": ["1 Other Road", "Blah"], "address_string": "1 Other Road Blah Blah Blah"}], "names": [{"type": "Private Individual", "private": {"forenames": ["Mister"], "surname": "Bankrupt"}}, {"type": "Private Individual", "private": {"forenames": ["Mr"], "surname": "Bankrupt"}}], "occupation": "Truck Driver"}], "class_of_charge": "WOB", "update_registration": {"type": "Amendment"}, "applicant": {"key_number": "1234567", "name": "S & H Legal Group", "address_type": "NA", "address": "49 Camille Circles Port Eulah PP39 6BY", "reference": " "}}'




further_amendment = '{"parties": [{"residence_withheld": false, "trading_name": " ", "legal_body_ref_no": "123 of 2016", "legal_body": "Devon County Court", "type": "Debtor", "case_reference": "Devon County Court 123 of 2016", "addresses": [{"type": "Residence", "postcode": "Blah", "county": "Blah", "address_lines": ["1 Other Road", "Blah"], "address_string": "1 Other Road Blah Blah Blah"}], "names": [{"type": "Private Individual", "private": {"forenames": ["Mister"], "surname": "Bankrupt"}}], "occupation": "Truck Driver"}], "class_of_charge": "WOB", "update_registration": {"type": "Amendment"}, "applicant": {"key_number": "1234567", "name": "S & H Legal Group", "address": "49 Camille Circles Port Eulah PP39 6BY", "reference": " "}}'

lc_api = RestAPI.new($LAND_CHARGES_URI)
pab_reg = register(pab_1)
wob_reg = register(wob_1)

amend_data = '{"pab_amendment": {"reg_no": "' + pab_reg['number'].to_s + '", "date": "' + pab_reg['date'] + '"},' + amendment_add_name

amend = lc_api.put("/registrations/#{wob_reg['date']}/#{wob_reg['number']}", amend_data)
amd_no = amend['new_registrations'][0]['number']
amd_date = amend['new_registrations'][0]['date']

# furth_amend = lc_api.put("/registrations/#{amd_date}/#{amd_no}", furth_amendment)
# puts furth_amend


# puts amend
# pab_reg = lc_api.put("/registrations/#{pab_reg['date']}/#{pab_reg['number']}", correction_1_name)
# puts reg2

# reg2['new_registrations'].each do |rect|
#     puts rect['date']
#     puts rect['number']
# end
# {"new_registrations"=>[{"name"=>{"type"=>"Private Individual", "private"=>{"surname"=>"Bankrupt", "forenames"=>["Mister"]}}, "number"=>1002, "date"=>"2016-03-09"}], "amended_registrations"=>[{"number"=>"1001", "date"=>"2016-03-09", "sequence"=>1}], "request_id"=>193}