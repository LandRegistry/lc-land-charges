require 'net/http'
require 'json'

uri = URI(ENV['BANKRUPTCY_REGISTRATION_URI'] || 'http://localhost:5004')
http = Net::HTTP.new(uri.host, uri.port)

response = http.request(Net::HTTP::Delete.new('/registrations'))
response = http.request(Net::HTTP::Delete.new('/area_variants'))