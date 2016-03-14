

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
    reg1 = lc_api.post('/registrations', data)

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
wob_regn_1_name = '{"applicant": {"name": "Waste of space", "address": "2 New Street, My Town", "key_number": "1234567", "reference": " "}, "parties":[{"names": [{"type": "Private Individual", "private": {"forenames": ["John", "Alan"], "surname": "Smithe"}}], "trading_name": " ", "addresses": [{"county": "Devon", "address_lines": ["2 new street", "Plymouth"], "postcode": "PL3 3PL", "type": "Residence", "address_string": "2 new street Plymouth Devon PL3 3PL"}, {"county": "Dorset", "address_lines": ["3 apple Street", "plymouth", "a third line", "a fourth line", "a five line"], "postcode": "postcode", "type": "Residence", "address_string": "3 apple Street plymouth a third line a fourth line a five line Cornwall postcode"}], "occupation": "", "type": "Debtor", "residence_withheld": false, "case_reference": "Plympton County Court 111 of 2016", "legal_body": "Plympton County Court", "legal_body_ref_no": "111 of 2016", "legal_body_ref_year": 2016, "counties": ["Devon", "Dorset"]}], "class_of_charge": "WOB"}'


correction_1_name = '{"update_registration": {"type": "Correction"}, "class_of_charge": "WOB", "applicant": {"reference": " ", "name": "Waste of space", "key_number": "1234567", "address": "2 New Street, My Town"}, "parties": [{"case_reference": "Plympton County Court 111 of 2016", "addresses": [{"county": "Devon", "postcode": "PL3 3PL", "type": "Residence", "address_lines": ["2 new street", "Plymouth"], "address_string": "2 new street Plymouth Devon PL3 3PL"}, {"county": "Dorset", "postcode": "postcode", "type": "Residence", "address_lines": ["3 apple Street", "plymouth", "a third line", "a fourth line", "a five line"], "address_string": "3 apple Street plymouth a third line a fourth line a five line Dorset postcode"}], "legal_body_ref_no": "111 of 2016", "occupation": "Lunatic", "residence_withheld": false, "trading_name": " ", "type": "Debtor", "legal_body": "Plympton County Court", "names": [{"type": "Private Individual", "private": {"forenames": ["John", "Alan"], "surname": "Smithe"}}]}]}'


wob_regn_2_names = '{"applicant": {"name": "Waste of space", "address": "2 New Street, My Town", "key_number": "1234567", "reference": " "}, "parties":[{"names": [{"type": "Private Individual", "private": {"forenames": ["John"], "surname": "Smith" }}, {"type": "Private Individual", "private": {"forenames": ["John", "Alan"], "surname": "Smithe"}}], "trading_name": " ", "addresses": [{"county": "Devon", "address_lines": ["2 new street", "Plymouth"], "postcode": "PL3 3PL", "type": "Residence", "address_string": "2 new street Plymouth Devon PL3 3PL"}, {"county": "Dorset", "address_lines": ["3 apple Street", "plymouth", "a third line", "a fourth line", "a five line"], "postcode": "postcode", "type": "Residence", "address_string": "3 apple Street plymouth a third line a fourth line a five line Cornwall postcode"}], "occupation": "", "type": "Debtor", "residence_withheld": false, "case_reference": "Plympton County Court 111 of 2016", "legal_body": "Plympton County Court", "legal_body_ref_no": "111 of 2016", "legal_body_ref_year": 2016, "counties": ["Devon", "Dorset"]}], "class_of_charge": "WOB"}'


correction_2_names = '{"update_registration": {"type": "Correction"}, "class_of_charge": "WOB", "applicant": {"reference": " ", "name": "Waste of space", "key_number": "1234567", "address": "2 New Street, My Town"}, "parties": [{"case_reference": "Plympton County Court 111 of 2016", "addresses": [{"county": "Devon", "postcode": "PL3 3PL", "type": "Residence", "address_lines": ["2 new street", "Plymouth"], "address_string": "2 new street Plymouth Devon PL3 3PL"}, {"county": "Dorset", "postcode": "postcode", "type": "Residence", "address_lines": ["3 apple Street", "plymouth", "a third line", "a fourth line", "a five line"], "address_string": "3 apple Street plymouth a third line a fourth line a five line Dorset postcode"}], "legal_body_ref_no": "111 of 2016", "occupation": "Lunatic", "residence_withheld": false, "trading_name": " ", "type": "Debtor", "legal_body": "Plympton County Court", "names": [{"type": "Private Individual", "private": {"forenames": ["John"], "surname": "Smith"}}, {"type": "Private Individual", "private": {"forenames": ["John", "Alan"], "surname": "Smithe"}}]}]}'

lc_api = RestAPI.new($LAND_CHARGES_URI)
reg = register(wob_regn_2_names)

reg2 = lc_api.put("/registrations/#{reg['date']}/#{reg['number']}", correction_2_names)
puts reg2

reg2['new_registrations'].each do |rect|
    puts rect['date']
    puts rect['number']
end