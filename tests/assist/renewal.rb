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



initial = '{"particulars": {"description": "1 The Lane, Some Village", "counties": ["Devon"], "district": "South Hams"}, "class_of_charge": "PA", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Johnson", "forenames": ["Jo", "John"]}}]}]}'

renewal = '{"class_of_charge": "PA", "applicant": {"name": "P334 Team", "reference": "reference 11", "address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095"}, "particulars": {"description": "1 Lane, Some Village", "district": "South Hams", "counties": ["Devon"]}, "parties": [{"names": [{"type": "Private Individual", "private": {"surname": "Johnson", "forenames": ["Jo", "John"]}}], "type": "Estate Owner"}], "update_registration": {"type": "Renewal"}}'

lc_api = RestAPI.new($LAND_CHARGES_URI)
reg = register(initial)

reg2 = lc_api.put("/registrations/#{reg['date']}/#{reg['number']}", renewal)
puts reg2

reg = reg2['new_registrations'][0]
reg3 = lc_api.put("/registrations/#{reg['date']}/#{reg['number']}", renewal)
puts reg3
