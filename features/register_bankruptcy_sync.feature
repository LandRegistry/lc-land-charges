Feature: Register a Bankruptcy & Synchronise

Scenario: Register a standard bankruptcy & sync

Given anything
When I submit valid data to the registration system
Then it returns a 200 OK response
And it returns the new registration number
And a new record is stored on the database
And the data is recorded on DB2
