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

`reset-data`

rectify = '{"class_of_charge": "C1", "applicant": {"name": "P334 Team", "reference": "reference 11", "address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095"}, "particulars": {"description": "1 The Lane, Some Village", "district": "South Hams", "counties": ["Devon"]}, "parties": [{"names": [{"type": "Private Individual", "private": {"surname": "Johnson", "forenames": ["Jo", "John"]}}], "type": "Estate Owner"}], "update_registration": {"type": "Rectification"}}'

lc_api = RestAPI.new($LAND_CHARGES_URI)
reg1 = lc_api.put("/registrations/2014-08-01/1003", rectify)
puts reg1

reg1['new_registrations'].each do |rect|
    puts rect['date']
    puts rect['number']
end
