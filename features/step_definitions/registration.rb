require 'net/http'
require 'json'
require 'rspec'
require 'pg'

no_alias = '{"key_number":"9056267","application_type":"PA(B)","application_ref":"9763603","date":"2014-11-12","debtor_name":{"forenames":["Lamar","Sigmund"],"surname":"Effertz"},"debtor_alternative_name":[],"gender":"N/A","occupation":"Ship builder","residence":[{"address_lines":["942 Carley Unions","Cullenberg","Dimitrimouth","Buckinghamshire"],"postcode":"QF47 0HG"}],"residence_withheld":false,"business_address":{"address_lines":["122 Leuschke Creek","Alvaburgh","Fife"],"postcode":"NO03 1EU"},"date_of_birth":"1974-10-03","investment_property":[]}'

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
        request = Net::HTTP::Post.new(url)
        request.body = data
        request["Content-Type"] = "application/json"
        @response = @http.request(request)
        @data = JSON.parse(@response.body)
    end
end

class PostgreSQL
	def self.connect
		@@pg = PGconn.connect( 'localhost', 5432,  '', '', 'landcharges', 'vagrant', 'vagrant')
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
	registration_api.post_data("/register", no_alias)
end

Then(/^it returns a 200 OK response$/) do
	expect(registration_api.response.code).to eql "200"
end

Then(/^it returns the new registration number$/) do
	assert(registration_api.data["new_registrations"].length == 1)
	puts registration_api.data
end

Then(/^a new record is stored on the database$/) do
	PostgreSQL.connect
	registration_api.data["new_registrations"].each do |reg_no|		
		result = PostgreSQL.query("SELECT * FROM register WHERE registration_no=#{reg_no}")
		expect(result.values.length).to be 1		
	end
	PostgreSQL.disconnect
end
