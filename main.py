import os
import json
import csv
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_data(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file)

def add_protein_type(protein_types):
    protein_type = input("Enter a new protein type: ")
    protein_types.append(protein_type)
    print(f"Protein type {protein_type} added.")
    save_data(protein_types, "protein_types.txt")

def add_protein(data, protein_types):
    today = datetime.today().strftime('%Y-%m-%d')
    date = input(f"Enter the date (YYYY-MM-DD) or press Enter to use today's date ({today}): ")
    if date == '':
        date = today
    print("Select a protein type:")
    for i, protein_type in enumerate(protein_types, start=1):
        print(f"{i}. {protein_type}")
    print(f"{len(protein_types) + 1}. Other")
    choice = int(input("Choose an option: "))
    if choice <= len(protein_types):
        protein_type = protein_types[choice - 1]
    else:
        protein_type = input("Enter the type of protein: ")
    grams = int(input("Enter the amount of protein in grams: "))
    data.append({"date": date, "protein_type": protein_type, "grams": grams})
    save_data(data, "protein_data.txt")

def view_protein(data):
    today = datetime.today().strftime('%Y-%m-%d')
    date = input(f"Enter the date (YYYY-MM-DD) or press Enter to use today's date ({today}): ")
    if date == '':
        date = today
    total = 0
    for entry in data:
        if entry["date"] == date:
            print(f"{entry['grams']}g of {entry['protein_type']}")
            total += entry["grams"]
    print(f"Total protein consumed on {date}: {total}g")

def export_csv(data):
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")
    filename = f"protein_{start_date}_to_{end_date}.csv"
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Protein Type", "Grams"])
        for entry in data:
            if start_date <= entry["date"] <= end_date:
                writer.writerow([entry["date"], entry["protein_type"], entry["grams"]])
    print(f"Data exported to {filename}")

def edit_entry(data):
    today = datetime.today().strftime('%Y-%m-%d')
    date = input(f"Enter the date of the entry you want to edit (YYYY-MM-DD) or press Enter to use today's date ({today}): ")
    if date == '':
        date = today
    for i, entry in enumerate(data):
        if entry["date"] == date:
            print(f"{i+1}. {entry['grams']}g of {entry['protein_type']}")
    entry_no = int(input("Enter the number of the entry you want to edit: ")) - 1
    data[entry_no]["protein_type"] = input("Enter the new type of protein: ")
    data[entry_no]["grams"] = int(input("Enter the new amount of protein in grams: "))
    save_data(data, "protein_data.txt")

def main():
    protein_data = load_data("protein_data.txt")
    protein_types = load_data("protein_types.txt")
    while True:
        clear_screen()
        print("\nProtein Tracker V.01\n")
        print("1. Add protein consumption")
        print("2. View protein consumption")
        print("3. Add protein type")
        print("4. Export data to CSV")
        print("5. Edit an entry")
        print("6. Exit")
        choice = input("\nChoose an option: ")
        if choice == "1":
            add_protein(protein_data, protein_types)
        elif choice == "2":
            view_protein(protein_data)
        elif choice == "3":
            add_protein_type(protein_types)
        elif choice == "4":
            export_csv(protein_data)
        elif choice == "5":
            edit_entry(protein_data)
        elif choice == "6":
            break
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
