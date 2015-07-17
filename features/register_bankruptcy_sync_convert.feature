Feature: Register a Bankruptcy & Synchronise/Convert

Scenario: Register a standard bankruptcy & sync/convert

Given anything
When I submit Bob Howard to the registration system
Then it returns a 200 OK response
And it returns the new registration number
And a new record is stored on the database
And the data is recorded on DB2
And the name has been correctly transformed
And the class of bankruptcy is correctly recorded
