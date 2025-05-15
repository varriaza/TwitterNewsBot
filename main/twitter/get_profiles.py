import csv
from pathlib import Path

def get_people_usernames() -> list[str]:
    """
    Reads the people.csv file and returns a list of Twitter usernames.
    
    Returns:
        list[str]: List of Twitter usernames from people.csv
    """
    usernames = []
    csv_path = Path(__file__).parent / "profiles" / "people.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            usernames.append(row['Twitter Handle'])
    
    return usernames

def get_organization_usernames() -> list[str]:
    """
    Reads the organizations.csv file and returns a list of Twitter usernames.
    
    Returns:
        list[str]: List of Twitter usernames from organizations.csv
    """
    usernames = []
    csv_path = Path(__file__).parent / "profiles" / "organizations.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            usernames.append(row['Twitter Handle'])
    
    return usernames
