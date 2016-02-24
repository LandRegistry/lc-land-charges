require 'net/http'
require 'json'

uri = URI(ENV['LAND_CHARGES_URI'] || 'http://localhost:5004')
http = Net::HTTP.new(uri.host, uri.port)

counties = counties = '[' +
    '{ "eng": "Bath and NE Somerset" },' +
    '{ "eng": "Bedford" },' +
    '{ "eng": "Blackburn with Darwen" },' +
    '{ "eng": "Blackpool" },' +
    '{ "eng": "Bournemouth" },' +
    '{ "eng": "Bracknell Forest" },' +
    '{ "eng": "Brighton & Hove" },' +
    '{ "eng": "Bristol (city of)" },' +
    '{ "eng": "Buckinghamshire" },' +
    '{ "eng": "Cambridgeshire" },' +
    '{ "eng": "Central Bedfordshire" },' +
    '{ "eng": "Cheshire East" },' +
    '{ "eng": "Cheshire West & Chester" },' +
    '{ "eng": "Cornwall (including Isles of Scilly)" },' +
    '{ "eng": "County Durham" },' +
    '{ "eng": "Cumbria" },' +
    '{ "eng": "Darlington" },' +
    '{ "eng": "Derby (city of)" },' +
    '{ "eng": "Derbyshire" },' +
    '{ "eng": "Devon" },' +
    '{ "eng": "Dorset" },' +
    '{ "eng": "East Riding of Yorkshire" },' +
    '{ "eng": "East Sussex" },' +
    '{ "eng": "Essex" },' +
    '{ "eng": "Gloucestershire" },' +
    '{ "eng": "Greater London" },' +
    '{ "eng": "Greater Manchester" },' +
    '{ "eng": "Halton" },' +
    '{ "eng": "Hampshire" },' +
    '{ "eng": "Hartlepool" },' +
    '{ "eng": "Herefordshire" },' +
    '{ "eng": "Hertfordshire" },' +
    '{ "eng": "Isle of Wight" },' +
    '{ "eng": "Kent" },' +
    '{ "eng": "Kingston upon Hull (city of)" },' +
    '{ "eng": "Lancashire" },' +
    '{ "eng": "Leicester" },' +
    '{ "eng": "Leicestershire" },' +
    '{ "eng": "Lincolnshire" },' +
    '{ "eng": "Luton" },' +
    '{ "eng": "Medway" },' +
    '{ "eng": "Merseyside" },' +
    '{ "eng": "Middlesbrough" },' +
    '{ "eng": "Milton Keynes" },' +
    '{ "eng": "Norfolk" },' +
    '{ "eng": "North East Lincolnshire" },' +
    '{ "eng": "North Somerset" },' +
    '{ "eng": "North Yorkshire" },' +
    '{ "eng": "Northamptonshire" },' +
    '{ "eng": "Northumberland" },' +
    '{ "eng": "Nottingham (city of)" },' +
    '{ "eng": "Nottinghamshire" },' +
    '{ "eng": "Oxfordshire" },' +
    '{ "eng": "Peterborough (city of)" },' +
    '{ "eng": "Plymouth (city of)" },' +
    '{ "eng": "Poole" },' +
    '{ "eng": "Portsmouth" },' +
    '{ "eng": "Reading" },' +
    '{ "eng": "Redcar and Cleveland" },' +
    '{ "eng": "Rutland" },' +
    '{ "eng": "Salop (Shropshire)" },' +
    '{ "eng": "Slough" },' +
    '{ "eng": "Somerset" },' +
    '{ "eng": "South Gloucestershire" },' +
    '{ "eng": "South Yorkshire" },' +
    '{ "eng": "Southampton" },' +
    '{ "eng": "Southend on Sea" },' +
    '{ "eng": "Staffordshire" },' +
    '{ "eng": "Stockton on Tees" },' +
    '{ "eng": "Stoke on Trent" },' +
    '{ "eng": "Suffolk" },' +
    '{ "eng": "Surrey" },' +
    '{ "eng": "Swindon" },' +
    '{ "eng": "Thurrock" },' +
    '{ "eng": "Torbay" },' +
    '{ "eng": "Tyne and Wear" },' +
    '{ "eng": "Warrington" },' +
    '{ "eng": "Warwickshire" },' +
    '{ "eng": "West Berkshire" },' +
    '{ "eng": "West Midlands" },' +
    '{ "eng": "West Sussex" },' +
    '{ "eng": "West Yorkshire" },' +
    '{ "eng": "Wiltshire" },' +
    '{ "eng": "Windsor & Maidenhead" },' +
    '{ "eng": "Wokingham" },' +
    '{ "eng": "Worcestershire" },' +
    '{ "eng": "Wrekin" },' +
    '{ "eng": "York" },' +
    '{ "eng": "Blaenau Gwent", "cym": "Blaenau Gwent" },' +
    '{ "eng": "Bridgend", "cym": "Pen-y-Bont ar Ogwr" },' +
    '{ "eng": "Caerphilly", "cym": "Caerffili" },' +
    '{ "eng": "Cardiff", "cym": "Sir Caerdydd" },' +
    '{ "eng": "Carmarthenshire", "cym": "Sir Gaerfyrddin" },' +
    '{ "eng": "Ceredigion", "cym": "Sir Ceredigion" },' +
    '{ "eng": "Conwy", "cym": "Conwy" },' +
    '{ "eng": "Denbighshire", "cym": "Sir Ddinbych" },' +
    '{ "eng": "Flintshire", "cym": "Sir y Fflint" },' +
    '{ "eng": "Gwynedd", "cym": "Gwynedd" },' +
    '{ "eng": "Isle of Anglesey", "cym": "Sir Ynys Mon" },' +
    '{ "eng": "Merthyr Tydfil", "cym": "Merthyr Tudful" },' +
    '{ "eng": "Monmouthshire", "cym": "Sir Fynwy" },' +
    '{ "eng": "Neath Port Talbot", "cym": "Castell-Nedd Port Talbot" },' +
    '{ "eng": "Newport", "cym": "Casnewydd" },' +
    '{ "eng": "Pembrokeshire", "cym": "Sir Benfro" },' +
    '{ "eng": "Powys", "cym": "Powys" },' +
    '{ "eng": "Rhondda Cynon Taff", "cym": "Rhondda Cynon Taf" },' +
    '{ "eng": "Swansea", "cym": "Sir Abertawe" },' +
    '{ "eng": "The Vale of Glamorgan", "cym": "Bro Morgannwg" },' +
    '{ "eng": "Torfaen", "cym": "Tor-Faen" },' +
    '{ "eng": "Wrexham", "cym": "Wrecsam" }' +
']'

request = Net::HTTP::Post.new('/counties')
request.body = counties
request["Content-Type"] = "application/json"
response = http.request(request)
if response.code != "200"
    puts "banks-reg/counties: #{response.code}"
end

folder = File.dirname(__FILE__)
county_data = File.readlines("#{folder}/counties.csv")
data = []
ref_nums = {}
refs = 0
county_data.each do |line|
    line_array = line.split(',')

    data.push({
        'name' => line_array[0],
        'key' => line_array[2],
        'variant_of' => line_array[1],
        'county_council' => (line_array[3] == 'Y')
    })
end

request = Net::HTTP::Put.new('/area_variants')
request.body = JSON.dump(data)
request["Content-Type"] = "application/json"
response = http.request(request)
if response.code != "200"
    puts "land-charges/area_variants: #{response.code}"
end




standard_data = [
    '{"applicant": {"address": "[INS PLACEHOLDER HERE! FIXME]", "name": "[INS PLACEHOLDER HERE! FIXME]", "reference": "APP01", "key_number": "1234567"}, "parties": [{"case_reference": "[WHAT GOES HERE] FIXME!", "trading_name": "", "residence_withheld": false, "date_of_birth": "1980-01-01", "names": [{"private": {"forenames": ["Bob", "Oscar", "Francis"], "surname": "Howard"}, "type": "Private Individual"}], "occupation": "Civil Servant", "addresses": [{"address_lines": ["1 The Street", "The Town"], "county": "The County", "postcode": "AA1 1AA", "type": "Residence"}], "type": "Debtor"}], "class_of_charge": "PAB"}',
    '{"applicant": {"address": "[INS PLACEHOLDER HERE! FIXME]", "name": "[INS PLACEHOLDER HERE! FIXME]", "reference": "APP02", "key_number": "1234567"}, "parties": [{"case_reference": "[WHAT GOES HERE] FIXME!", "trading_name": "", "residence_withheld": false, "date_of_birth": "1980-01-01", "names": [{"private": {"forenames": ["Alphonso", "Alice"], "surname": "Schmidt"}, "type": "Private Individual"}, {"private": {"forenames": ["Bert"], "surname": "Smith"}, "type": "Private Individual"}], "occupation": "Civil Servant", "addresses": [{"address_lines": ["1 The Street", "The Locality", "The Town"], "county": "The County", "postcode": "AA1 1AA", "type": "Residence"}], "type": "Debtor"}], "class_of_charge": "PAB"}',
    '{"particulars": {"description": "1 The Lane, Some Village", "counties": ["Devon"], "district": "South Hams"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Johnson", "forenames": ["Jo", "John"]}}]}]}',
    '{"particulars": {"description": "Flat A, Floor 15, The Hideous Tower, Cityname", "counties": ["Dorset", "Lancashire"], "district": "Mixed"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "County Council", "local": {"area": "Lancs", "name": "South Marsh District Council"}}]}]}',
    '{"priority_notice": {"expires": "2014-12-12"}, "particulars": {"description": "1 The Lane, Some Village", "counties": ["Devon"], "district": "South Hams"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Bobson", "forenames": ["Bob", "John"]}}]}]}',
    '{"priority_notice": {"expires": "2100-01-01"}, "particulars": {"description": "1 The Lane, Some Village", "counties": ["Devon"], "district": "South Hams"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Hughson", "forenames": ["Hugh", "John"]}}]}]}',
    '{"priority_notice": {"expires": "2016-02-01"}, "particulars": {"description": "EXPIRE 2016-02-01 1 The Lane, Some Village", "counties": ["Devon"], "district": "South Hams"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Expires", "forenames": ["Test", "Notice"]}}]}]}',
    '{"priority_notice": {"expires": "2100-01-01"}, "particulars": {"description": "EXPIRE 2100s 1 The Street, Some Town", "counties": ["Dorset"], "district": "South Hams"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Expires", "forenames": ["Test", "Notice"]}}]}]}',
    '{"priority_notice": {"expires": "2100-01-01"}, "particulars": {"description": "EXPIRE 2100s.2 1 The Street, Some Town", "counties": ["Dorset"], "district": "South Hams"}, "class_of_charge": "C1", "applicant": {"address": "Land Registry Information Systems, 2 William Prance Road, Plymouth", "key_number": "244095", "name": "P334 Team", "reference": "reference 11"}, "parties": [{"type": "Estate Owner", "names": [{"type": "Private Individual", "private": {"surname": "Expires", "forenames": ["Test", "Notice"]}}]}]}',
    '{"applicant": {"name": "Waste of space", "address": "2 New Street, My Town", "key_number": "1234567", "reference": " "}, "parties":[{"names": [{"type": "Private Individual", "private": {"forenames": ["John"], "surname": "Smith" }}, {"type": "Private Individual", "private": {"forenames": ["John", "Alan"], "surname": "Smithe"}}], "trading_name": " ", "addresses": [{"county": "Devon", "address_lines": ["2 new street", "Plymouth"], "postcode": "PL3 3PL", "type": "Residence", "address_string": "2 new street Plymouth Devon PL3 3PL"}, {"county": "Dorset", "address_lines": ["3 apple Street", "plymouth", "a third line", "a fourth line", "a five line"], "postcode": "postcode", "type": "Residence", "address_string": "3 apple Street plymouth a third line a fourth line a five line Cornwall postcode"}], "occupation": "", "type": "Debtor", "residence_withheld": false, "case_reference": "Plympton County Court 111 of 2016", "legal_body": "Plympton County Court", "legal_body_ref_no": "111", "legal_body_ref_year": 2016, "counties": ["Devon", "Dorset"]}], "class_of_charge": "PAB"}'
]

regn_dates = [
    '2014-06-03',
    '2014-07-02',
    '2014-08-01',
    '2014-09-29',
    '2014-11-02',
    '2016-02-10',
    '2015-11-01',
    '2015-11-01',
    '2015-11-01',
    '2016-01-02',
]

standard_data.length.times do |i|
    item = standard_data[i]
    date = regn_dates[i]

    request = Net::HTTP::Post.new('/registrations?suppress_queue=yes&dev_date=' + date)
    request.body = item
    request["Content-Type"] = "application/json"
    response = http.request(request)
    if response.code != "200"
        puts "banks-reg/registrations: #{response.code}"
    end
end
