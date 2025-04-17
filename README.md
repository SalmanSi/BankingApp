
**Banking App**  
A semester‑project Django app that lives and breathes MySQL. I modeled customers, accounts, transactions and loans in a clean schema, then moved almost all the “business logic”—PIN checks, balance updates, transfers and loan approvals—into stored procedures so the database really does the heavy lifting.

**Highlights**  
- **Raw SQL & Stored Procs:** Everything from account creation to fund transfers runs inside MySQL for speed and clarity.  
- **Schema First:** Clear tables for branches, customers, accounts and transactions, with foreign keys gluing it all together.  
- **Easy Setup:** Import the SQL dump in `/Database/`, tweak your `settings.py`, then run Django’s server—no fuss.

Enjoy poking around the SQL code!
