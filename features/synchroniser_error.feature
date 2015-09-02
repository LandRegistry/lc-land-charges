@error
Feature: Synchroniser Error Handling

Scenario: Send Invalid Data to Synchroniser

Given I have registered a bankruptcy
When Invalid registration numbers are sent to the synchroniser
#Then it posts an error message to its error queue