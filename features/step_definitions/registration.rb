require 'net/http'
require 'json'
require 'rspec'
require 'pg'

no_alias = '{"key_number":"9056267","application_type":"PA(B)","application_ref":"9763603","date":"2014-11-12","debtor_name":{"forenames":["Lamar","Sigmund"],"surname":"Effertz"},"debtor_alternative_name":[],"gender":"N/A","occupation":"Ship builder","residence":[{"address_lines":["942 Carley Unions","Cullenberg","Dimitrimouth"],"county":"Buckinghamshire","postcode":"QF47 0HG"}],"residence_withheld":false,"business_address":{"address_lines":["122 Leuschke Creek","Alvaburgh"],"county":"Fife","postcode":"NO03 1EU"},"date_of_birth":"1974-10-03","investment_property":[]}'
one_alias = '{"key_number":"6269524","application_type":"PA(B)","application_ref":"7282631","date":"2015-02-19","debtor_name":{"forenames":["Helga","Nelda"],"surname":"Hessel"},"debtor_alternative_name":[{"forenames":["Nelda","Helga"],"surname":"Hessel"}],"gender":"N/A","occupation":"Flower arranger","residence":[{"address_lines":["45633 Wyman Corner","Huelshire","Lake Jennings"],"county":"West Yorkshire","postcode":"YL23 2FD"}],"residence_withheld":false,"business_address":{"address_lines":["423 Zander Mount","Konopelskifurt","South Shyannberg"],"county":"Shropshire","postcode":"AE64 7DF"},"date_of_birth":"1953-01-11","investment_property":[]}'
bob_howard = '{"key_number":"1479067","application_type":"PA(B)","application_ref":"9045789","date":"2014-10-28","debtor_name":{"forenames":["Bob","Oscar","Francis"],"surname":"Howard"},"debtor_alternative_name":[],"gender":"N/A","occupation":"Bookmaker","residence":[{"address_lines":["1940 Huels Fort","North Glennamouth","South Nonafort"],"county":"West Yorkshire","postcode":"PA85 4RH"}],"residence_withheld":false,"business_address":{"address_lines":["831 Hailee Burg","Chasityborough","East Tamara"],"county":"Northamptonshire","postcode":"IP81 2CM"},"date_of_birth":"1974-10-07","investment_property":[]}'

class AssertionFailure < RuntimeError
end

def assert( condition, message = nil ) 
    unless( condition ) 
        raise AssertionFailure, message
    end
end

class RestAPI
	attr_reader :response, :data

    def initialize(uri)
        @uri = URI(uri)
        @http = Net::HTTP.new(@uri.host, @uri.port)
    end
    
    def post_data(url, data)
		puts(data)
        request = Net::HTTP::Post.new(url)
        request.body = data
        request["Content-Type"] = "application/json"
        @response = @http.request(request)
        if @response.body == ""
			nil
        else
			@data = JSON.parse(@response.body)
		end
    end
    
    def get_data(url)
		request = Net::HTTP::Get.new(url)
		@response = @http.request(request)
		@data = JSON.parse(@response.body)
    end
end

class PostgreSQL
	def self.connect(database)
		@@pg = PGconn.connect( 'localhost', 5432,  '', '', database, 'vagrant', 'vagrant')
	end
	
	def self.disconnect
		@@pg.close
	end
	
	def self.query(sql)
		@@pg.exec(sql)
	end

end


Given(/^anything$/) do
end

registration_api = nil

When(/^I submit valid data to the registration system$/) do
	registration_api = RestAPI.new("http://localhost:5004")
	registration_api.post_data("/registration", no_alias)
end

Then(/^it returns a 200 OK response$/) do
	expect(registration_api.response.code).to eql "200"
end

Then(/^it returns the new registration number$/) do
	assert(registration_api.data["new_registrations"].length == 1)
	puts registration_api.data
end

Then(/^a new record is stored on the database$/) do
	PostgreSQL.connect('landcharges')
	registration_api.data["new_registrations"].each do |reg_no|		
		result = PostgreSQL.query("SELECT * FROM register WHERE registration_no=#{reg_no}")
		expect(result.values.length).to be 1		
	end
	PostgreSQL.disconnect
end

When(/^I submit valid data with an alias to the registration system$/) do
	registration_api = RestAPI.new("http://localhost:5004")
	registration_api.post_data("/registration", one_alias)
end

Then(/^it returns the (\d+) new registration numbers$/) do |arg1|
	assert(registration_api.data["new_registrations"].length.to_s == arg1)
end

Then(/^(\d+) new records are stored on the database$/) do |arg1|
	PostgreSQL.connect('landcharges')
	c = 0
	registration_api.data["new_registrations"].each do |reg_no|		
		result = PostgreSQL.query("SELECT * FROM register WHERE registration_no=#{reg_no}")
		expect(result.values.length).to be 1		
		c += 1
	end
	expect(c.to_s).to eql arg1
	PostgreSQL.disconnect
end

Then(/^the data is recorded on DB2$/) do
	sleep(1)
	PostgreSQL.connect('db2')
	registration_api.data["new_registrations"].each do |reg_no|
		reg_str = reg_no.to_s.rjust(8)
		print(reg_str)
		result = PostgreSQL.query("SELECT * FROM lc_mock WHERE registration_no='#{reg_str}'")
		expect(result.values.length).to eq 1		
	end
	PostgreSQL.disconnect
end

When(/^I submit Bob Howard to the registration system$/) do
	registration_api = RestAPI.new("http://localhost:5004")
	registration_api.post_data("/registration", bob_howard)
end

Then(/^the name has been correctly transformed$/) do
	PostgreSQL.connect('db2')
	registration_api.data["new_registrations"].each do |reg_no|
		reg_str = reg_no.to_s.rjust(8)
		result = PostgreSQL.query("SELECT reverse_name, remainder_name, punctuation_code FROM lc_mock WHERE registration_no='#{reg_str}'")
		expect(result.values.length).to eq 1
		row = result.values[0]
		expect(row[0]).to eq "DRAWOHSICNAR"
		expect(row[1]).to eq "BOBOSCARF"
		expect(row[2]).to eq "2325C7"
	end
	PostgreSQL.disconnect  
end

Then(/^the class of bankruptcy is correctly recorded$/) do
	PostgreSQL.connect('db2')
	registration_api.data["new_registrations"].each do |reg_no|
		reg_str = reg_no.to_s.rjust(8)
		result = PostgreSQL.query("SELECT class_type FROM lc_mock WHERE registration_no='#{reg_str}'")
		expect(result.values.length).to eq 1
		row = result.values[0]
		expect(row[0]).to eq "PA(B)"
	end
	PostgreSQL.disconnect  
end

Given(/^I have registered a bankruptcy$/) do
end

When(/^Invalid registration numbers are sent to the synchroniser$/) do
	registration_api = RestAPI.new("http://localhost:5004")
	registration_api.post_data("/synchronise", '["42"]')
	sleep(1)
end

Then(/^it posts an error message to its error queue$/) do
	error_api = RestAPI.new("http://localhost:5006")
	result = error_api.get_data("/errors").last
	expect(result['source']).to eq 'Synchroniser'
	expect(result['data']['registration_no']).to eq '42'
	expect(result['data']['status_code']).to eq 404
	expect(result['data']['uri']).to eq '/registration'
end
