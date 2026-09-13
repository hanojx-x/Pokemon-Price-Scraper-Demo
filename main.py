from bs4 import BeautifulSoup
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
#list of selectable sets
SETS = {
    "Pokemon Base Set": "pokemon-base-set",
    "Pokemon Jungle": "pokemon-jungle",
    "Pokemon Fossil": "pokemon-fossil",
    "Pokemon Team Rocket": "pokemon-team-rocket",
    "Pokemon Gym Heroes": "pokemon-gym-heroes",
    "Pokemon Gym Challenge": "pokemon-gym-challenge",
    "Pokemon Neo Genesis": "pokemon-neo-genesis",
    "Pokemon Neo Discovery": "pokemon-neo-discovery",
    "Pokemon Legendary Collection": "pokemon-legendary-collection",
    "Pokemon Base Set 2": "pokemon-base-set-2",
}
#scraper method: connects to pricecharting.com and gathers data from each column
def searcher(search_term):
    url = f"https://www.pricecharting.com/console/{search_term}"
    #requests gets the url above to scrape
    try:
        page = requests.get(url).text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to connect to PriceCharting: {e}")
        return [], [], [], []
    #initialize BeautifulSoup
    soup = BeautifulSoup(page, "html.parser")
    table = soup.find("table")

    #stores the values for each card
    card = [] #name of the card
    ungraded = [] #cost of ungraded card
    gr9 = [] #cost of PSA 9 graded card
    psa10 = [] #cost of PSA 10 graded card

    #finds values from the website's table
    if table:
        for row in table.find_all('tr'):
            cells = row.find_all('td')

            if len(cells) == 6:
                col2_card = cells[1].text.strip()
                col3_ungraded = cells[2].text.strip().replace("$","").replace(",","") #gets rid of symbols to prevent string values
                col4_gr9 = cells[3].text.strip().replace("$","").replace(",","")
                col5_psa10 = cells[4].text.strip().replace("$","").replace(",","")
                #adds data from columns to value arrays
                if col4_gr9 != "" and col5_psa10 != "":
                    card.append(col2_card)
                    ungraded.append(col3_ungraded)
                    gr9.append(col4_gr9)
                    psa10.append(col5_psa10)

    return card, ungraded, gr9, psa10

#opens the window if you select "View Prices"
def open_table_window(selected_set_name):
    #set chosen based on parameter
    selected_set = SETS[selected_set_name]
    #window
    list_window = tk.Toplevel(root)
    list_window.title(f"Set: {selected_set_name}")
    list_window.geometry("700x500")
    #uses searcher to assign values to each column
    cards, ungraded, gr9, psa10 = searcher(selected_set)

    #searchbar
    search_frame = tk.Frame(list_window)
    search_frame.pack(fill="x", padx=10, pady=10)

    search_label = tk.Label(search_frame, text="Search for a card:", font=("Arial", 10, "bold"))
    search_label.pack(side="left", padx=5)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=35, font=("Arial", 10))
    search_entry.pack(side="left", padx=5)

    #treeview and column names
    columns = ("Card Name", "Ungraded", "Grade 9", "PSA 10")
    tree = ttk.Treeview(list_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(side="left", fill="both", expand=True)

    #populates tree with values
    def populate_tree(query=""):
        #clear current tree items
        for item in tree.get_children():
            tree.delete(item)
        #filters out all card names that don't belong (if searchbar is used)
        for i in range(len(cards)):
            card_name = cards[i]
            #case-insensitive
            if query.lower() in card_name.lower():
                g9_val = gr9[i]
                psa10_val = psa10[i]
                tree.insert("", "end", values=(card_name, ungraded[i], g9_val, psa10_val))
    #update the tree dynamically, w stands for "write"
    search_var.trace_add("write", lambda *args: populate_tree(search_var.get()))

    #populates tree
    populate_tree()

    #inserts values into tree
    for i in range(len(cards)):
        if gr9[i] == "":
            g9_val = "N/A"
        else:
            g9_val = gr9[i]
        if psa10[i] == "":
            psa10_val = "N/A"
        else:
            psa10_val = psa10[i]
        tree.insert("", "end", values=(cards[i], ungraded[i], g9_val, psa10_val))

#opens the window if you select "Set Statistics"
def open_stats_window(selected_set_name):
    selected_set = SETS[selected_set_name]
    #window
    list_window = tk.Toplevel(root)
    list_window.title(f"Stats for {selected_set_name}")
    list_window.geometry("700x500")
    #gathers info from searcher method
    cards, ungraded, gr9, psa10 = searcher(selected_set)

    #uses pandas dataframe to create columns
    df_wide = pd.DataFrame({
        "Card Name": cards,
        "Ungraded": ungraded,
        "Grade 9": gr9,
        "PSA 10": psa10
    })

    #melts data into a long dataframe, allowing for actual columns
    df = pd.melt(df_wide, id_vars=["Card Name"], value_vars=["Ungraded", "Grade 9", "PSA 10"], var_name="Grade", value_name="Value")
    df["Value"] = pd.to_numeric(df["Value"])

    #information for set statistics as well as the five most expensive cards
    set_stats = df.groupby(["Grade"])["Value"].agg(["mean", "median", "min", "max", "count"]).reset_index()
    top_cards = df.sort_values(by="Value", ascending=False).head(5)

    #STATS TREEVIEW
    stats_label = tk.Label(list_window, text="Grade Statistics Summary", font=("Arial", 12, "bold"))
    stats_label.pack(pady=5)

    stats_columns = ("Grade", "Mean", "Median", "Min", "Max", "Count")
    stats_tree = ttk.Treeview(list_window, columns=stats_columns, show="headings", height=3)
    for col in stats_columns:
        stats_tree.heading(col, text=col)
        stats_tree.column(col, width=90)
    stats_tree.pack(pady=5, fill="x", padx=10)

    #populate treeview
    for _, row in set_stats.iterrows():
        stats_tree.insert("", "end", values=(row["Grade"], f"${row['mean']:.2f}", f"${row['median']:.2f}", f"${row['min']:.2f}", f"${row['max']:.2f}", row["count"]))

    #TOP 5 TREEVIEW
    top5_label = tk.Label(list_window, text="Top 5 Most Expensive Cards", font=("Arial", 12, "bold"))
    top5_label.pack(pady=5)

    top_columns = ("Card Name", "Grade", "Value")
    top_tree = ttk.Treeview(list_window, columns=top_columns, show="headings", height=5)
    for col in top_columns:
        top_tree.heading(col, text=col)
        top_tree.column(col, width=180)
    top_tree.pack(pady=5, fill="x", padx=10)

    #populate treeview
    for _, row in top_cards.iterrows():
        top_tree.insert("", "end", values=(row["Card Name"],row["Grade"],f"${row['Value']:.2f}"
        ))

#makes sure a set is selected
def table_click():
    selected_set = dropdown.get()
    if selected_set in SETS:
        open_table_window(selected_set)
def stats_click():
    selected_set = dropdown.get()
    if selected_set in SETS:
        open_stats_window(selected_set)

root = tk.Tk()
root.title("Pokémon Price Scraper")
root.geometry("500x500")

title = tk.Label(root, text="Welcome to the Pokémon Price Scraper!", font=("Arial", 18, "bold"))
prompt = tk.Label(root, text="Select a Pokémon Set:", font=("Arial", 11))
title.pack(pady=100)
prompt.pack(pady=15)

dropdown = ttk.Combobox(root, values=list(SETS.keys()), state="readonly", width=30)
dropdown.pack(pady=15)

search_button = tk.Button(root, text="View Prices", command=table_click, width=15)
search_button.pack(pady=10)

stats_button = tk.Button(root, text="Set Statistics", command=stats_click, width=15)
stats_button.pack(pady=10)

root.mainloop()