# Guaranteed-Values-Calculator
Actuarial tool that compute guaranteed values for whole life, term, and endowment policies.


This project was born out of my work in the Actuarial Mathematics course during my fifth semester. I wanted to build something that didn’t just apply the formulas from the manual, but actually made them come alive — something that could calculate, visualize, and export the core values of life insurance policies in a clear, professional way.

After months of working through commutation tables, debugging formulas, and reading actuarial notes, I decided to turn everything into a functional web app using Python and Streamlit. It’s a practical calculator that computes Guaranteed Values for the three classic life insurance types: Whole Life, Term, and Endowment (Mixed) — including the Commercial Premium, Surrender Value, Paid-Up Insurance, and Extended Term Insurance.

Purpose and Background

The main goal was to simplify the calculation process that actuaries perform daily — taking the formulas from the Actuarial Mathematics Manual 2025 (pages 1–29) and automating them while keeping transparency.

Every result is backed by the Mexican Mortality Table 2000-I, and the system adjusts dynamically to the interest rate entered by the user. It’s not meant to replace actuarial judgment, but to speed up repetitive computations so that students (and professionals) can focus on interpretation instead of arithmetic.

Installation

If you want to try it yourself, here’s what I recommend:

Download Python 3.8 or later from python.org
.
When installing, make sure to check “Add Python to PATH”.

Once installed, open CMD or PowerShell and confirm everything works with:

python --version


Go to the folder where the project is saved and install the dependencies:

pip install -r requirements.txt


or, if you prefer, install them one by one:

pip install streamlit pandas numpy fpdf

Running the App

Run this command in the project folder:

streamlit run calculadora.py


In a few seconds, the browser will open automatically.
If not, you can open it manually at http://localhost:8501
.

When I first got it running, seeing the interface appear with all the parameters I had coded felt like the reward for all those late nights of debugging formulas.

How It Works

The app starts with a sidebar where you enter the main parameters:

Insurance type (Whole Life, Term, or Endowment).

Sum Assured (minimum of $10,000).

Interest rate between 0.01% and 10% (entered as a percentage).

Age of the insured (from 12 to 99 years).

Type of loadings (minimum or maximum).

Year for which you want to evaluate guaranteed values.

You also choose the coverage term and the premium payment period, and then press Calculate Guaranteed Values.

From there, the calculator uses the commutation functions automatically. The output appears in four tabs:

Commercial Premium – shows the PNU, level premium, and commercial premium.

Surrender Value – the value the insured can claim when surrendering the policy.

Paid-Up Insurance – a reduced sum assured when premiums stop but coverage continues.

Extended Term Insurance – the remaining coverage period if converted to term insurance.

All of it updates instantly and can be exported to a neat PDF report ready for presentation or submission.

About the Loadings

These were a whole topic by themselves. I added both minimum and maximum sets according to the manual:

Whole Life and Endowment:

Administration: 5/1000 – 7/1000

Collection: 5% – 7%

Acquisition: 5% per year (up to 100%)

Term Insurance:

Administration: 2/1000 – 3/1000

Collection: 5% – 7%

Acquisition: 3% per year (up to 60%)

At first, I underestimated how much these little adjustments would change the final results. It was a good reminder of how delicate actuarial balance sheets are.

Grading and Structure

In our course, each plan (Whole Life, Term, and Endowment) is worth 30 points, divided as:

5 for the Commercial Premium

7.5 for the Surrender Value

7.5 for the Paid-Up Insurance

10 for the Extended Term Insurance

The last 10 points come from generating the PDF report correctly. Altogether, this project represents 30% of the semester grade — but honestly, it’s worth much more as a learning experience.

Lessons Learned

Building this calculator wasn’t just about coding — it taught me how mathematics, logic, and finance come together in one model. I remember getting lost in the recursive parts of the commutation functions and feeling that frustration that only makes sense to actuaries.

But once I saw how the formulas produced realistic and consistent results across different ages, interest rates, and terms, it all made sense. This project helped me see life insurance not as abstract math, but as a structured promise that has to make sense financially and ethically.

Troubleshooting (from experience)

If you see “No module named 'streamlit'”, just run pip install streamlit.

If PDFs don’t generate, reinstall fpdf.

If the app doesn’t open, copy the address manually or use a different port:

streamlit run calculadora.py --server.port 8502


Windows sometimes blocks permissions; running CMD as Administrator usually fixes it.

I ran into every one of these issues at least once — and sometimes twice.

Sharing the Project

To share it, just compress the project folder into a ZIP and send it to someone else.
They can follow the same setup and it’ll run immediately.

If you want to make it public, it’s easy to deploy using Streamlit Cloud and GitHub.
Once it’s up, you get a free URL (for example: yourapp.streamlit.app) and anyone can use it — no installation required.

TechNotes

All commutation values (Dₓ, Nₓ, Mₓ, etc.) follow the structure from the Actuarial Mathematics Manual 2025.

The program assumes annual discrete premiums.

Extended term interpolation uses 365 days per year and 30 days per month.

Endowment plans automatically display survival benefits if applicable.

Conclusion

This calculator isn’t just a technical project; it’s a summary of what I’ve learned so far about how actuarial models hold real meaning when applied properly. Every number on the screen represents someone’s future security — and that’s what makes this field both rigorous and deeply human.

Creating it taught me patience, precision, and respect for the beauty of actuarial mathematics.
And, honestly, it made me proud to be part of a field where every calculation tells a story about life, time, and value.
