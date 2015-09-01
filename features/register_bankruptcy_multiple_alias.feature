@reg_bank_multiple_alias
Feature: Register a Bankruptcy With Aliases

Scenario: Register a bankruptcy with an alias

Given anything
When I submit valid data with an alias to the registration system
Then it returns a 200 OK response
And it returns the 2 new registration numbers
And 2 new records are stored on the database

