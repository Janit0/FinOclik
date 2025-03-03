from flask import Flask, render_template, request, send_from_directory,jsonify
import openai
import matplotlib.pyplot as plt
import os
import hashlib
import gc
import numpy as np
import pandas as pd
import nltk
from nltk import word_tokenize
import regex as re 
import json
import requests
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
# Initialize Matplotlib
plt.switch_backend('agg')  # Use non-GUI backend for Matplotlib

#Applying API key from OpenAI to integarte it with our Chat Bot
openai.api_key = "your own key"

#################Creation of app Folder to store our data#########################
app = Flask(__name__, static_folder='C:/Users/Janit/.spyder-py3/AIP_AI/static')

# File to store conversation history
conversation_file = r'C:/Users/Janit/.spyder-py3/AIP_AI/conversation_history.txt'

def load_conversation_history():
    try:
        with open(conversation_file, 'r') as file:
            return eval(file.read())
    except (IOError, SyntaxError):  # Handle file not found or invalid content
        return []

def save_conversation_history():
    with open(conversation_file, 'w') as file:
        file.write(repr(conversation_history))

# Initialize conversation history
conversation_history = load_conversation_history()

def reset_conversation_history():
    global conversation_history
    conversation_history = []
    save_conversation_history()

# Reset conversation history when the Flask application starts
# reset_conversation_history()

#Creating the default message 
if not conversation_history:
    conversation_history.append({"chatbot_response": "Hi, How can I assist you?"})
    save_conversation_history()

def get_chatbot_response(user_input_gfq):
    # Simple chatbot logic
    #Creating Query Text to give limited words answer
    QueryAsked = user_input_gfq.lower() + "  in less than 20 words in each number point restrict to 3 points "
    if user_input_gfq.lower() == "hi":
        response = "Hi there! How can I help you?"
    elif "how are you" in user_input_gfq.lower():
        response = "I'm good, thank you! How about you?"
    else :
        
        #Calling the 3.5GPT Turbo
        CommonListofWords = ["crytocurrency","interest","Interest","crypto","","invest","investment strategies","investment options","investment","bonds","portfolio","real estate","risk","diversification","diversify","retirement","retire","stocks","stock"]
        UserInputText = user_input_gfq.lower()
        UserInputText = UserInputText.split()
        
        #Creation of list comprehension
        DataListForCheckof_FinancialTerm = [item for item in UserInputText if item in CommonListofWords]
        
        if len(DataListForCheckof_FinancialTerm) > 0:
            completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": QueryAsked}])
            
            #Message Extracted From Chat GPT
            Message_ExtractedData = completion.choices[0].message.content
            
            response =  Message_ExtractedData
        
        else:
            response = "Sorry we only deal with financial queries. Please do try again."
    # Add the user input and chatbot response to the conversation history
    conversation_history.append({"user_input": user_input_gfq, "chatbot_response": response})
    
    # Save the updated conversation history
    save_conversation_history()
 
    return response

#####################Excel File Loading#####################3

# File to store conversation history for Fin0lyzer
fin0lyzer_conversation_file = r'C:/Users/Janit/.spyder-py3/AIP_AI/fin0lyzer_conversation_history.txt'

def load_fin0lyzer_conversation_history():
    try:
        if os.path.exists(fin0lyzer_conversation_file):
            with open(fin0lyzer_conversation_file, 'r') as file:
                return json.load(file)
        else:
            return []
    except (IOError, json.JSONDecodeError):  # Handle file not found or invalid content
        return []

def save_fin0lyzer_conversation_history():
    with open(fin0lyzer_conversation_file, 'w') as file:
        file.write(repr(fin0lyzer_conversation_history).replace("'", '"'))

# Initialize conversation history for Fin0lyzer
fin0lyzer_conversation_history = load_fin0lyzer_conversation_history()

# =============================================================================
# def reset_fin0lyzer_conversation_history():
#     global fin0lyzer_conversation_history
#     fin0lyzer_conversation_history = []
#     save_fin0lyzer_conversation_history()
# 
# #Reset conversation history when necessary
# reset_fin0lyzer_conversation_history()
# 
# =============================================================================
# =============================================================================
# if not fin0lyzer_conversation_history:
#     fin0lyzer_conversation_history.append({"chatbot_response": "Hi, Which Stock Are You Looking For?"})
# 
# =============================================================================
save_fin0lyzer_conversation_history()


#Function to acces data from Aplha Vantage Website

# Define global variables to store the data
def API_FuncCompanyData(symbol,api_key):
        
    TimeSeries_MonthlyAdjust = f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={api_key}'
    Earning = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&type=monthly&apikey={api_key}'
    Income_Stat = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={api_key}"
    
    #Requesting to access the data from the Alpha vantage API's
    response_TSM = requests.get(TimeSeries_MonthlyAdjust)
    response_Ear = requests.get(Earning)
    response_IS = requests.get(Income_Stat)
    
    data_TSM = response_TSM.json()
    data_Ear = response_Ear.json()
    data_IS = response_IS.json()
    
    return data_TSM,data_Ear,data_IS
    
#Reading the data extracted from A
Listing_Data = pd.read_csv("C:/Users/Janit/Downloads/listing_status (1).csv")

#Filtering out the Stocks Listed in NASDAQ
Listing_Data = Listing_Data[Listing_Data["exchange"] == "NASDAQ"]

#From that columns used will be ["symbol","name"]
Listing_Data = Listing_Data[Listing_Data["assetType"] == "Stock"][["symbol","name"]]

#Dropping NA rows as it can affect the data
Listing_Data.dropna(axis = 0,inplace = True)
Symbol_List = list(Listing_Data["symbol"])

#Extarcting initial letters from the symbols as in many situations companies name 
#and symbol they are assigned with have same starting letter.
#Eg: Apple has the symbol of AAPL. So, as we see Apple and AAPL the symbol of Apple
#starts with A. This helps in filtering data to avoid tarversing through 1000 of rows.

Listing_Data["Initial Letter"] = [Symbol_List[i][0] for i in range(len(Symbol_List))]

#Converting the name to upper for better check of stock name
Listing_Data["name"] = Listing_Data["name"].str.upper()

#Cleaning the data for some unwated symbolls,letters, stop words etc.
def data_clean(text):
    cleaned_text = re.sub(r'\b\.com\b', '', text)
    cleaned_text = re.sub(r'https?://\S+', '', text)
    cleaned_text = re.sub( r'@\w+', '', cleaned_text)
    cleaned_text = re.sub(r'#\w+', '', cleaned_text)
    cleaned_text = re.sub(r'\d+', '', cleaned_text)
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    cleaned_text = re.sub(r'^RT\s+', '', cleaned_text)
    cleaned_text = re.sub(r'[^a-zA-Z\s]', '', cleaned_text)
    cleaned_text = re.sub(r'\n+', '', cleaned_text)
    cleaned_text = re.sub(r':\)|:\(+', '', cleaned_text)
    cleaned_text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U0001FAC0-\U0001FAFF\U0001FB00-\U0001FBFF\U0001FC00-\U0001FCFF\U0001FD00-\U0001FDFF\U0001FE00-\U0001FEFF\U0001F200-\U0001F251]+', '', cleaned_text)
    return cleaned_text

#Applying the cleaning on the Company Name.
Listing_Data["name"] = Listing_Data["name"].apply(data_clean)

#Applying word tokenization to make each word as token which can help us identify the 
#company name
def word_tokenization(text):
    token = word_tokenize(text)
    return token
Listing_Data["Tokenized_Text"] = Listing_Data["name"].apply(word_tokenization)

Listing_Data.reset_index(inplace = True)
Listing_Data.drop("index",axis =1,inplace = True)

# Function to get chatbot response for Fin0lyzer
def get_fin0lyzer_chatbot_response(user_input_fin0lyzer):
    if user_input_fin0lyzer.lower() == "hi":
        response = "Hi there! How can I help you?"
    elif "how are you" in user_input_fin0lyzer.lower():
        response = "I'm good, thank you! How about you?"
    else:
        response = process_user_input(user_input_fin0lyzer)
        
        # Add the user input and chatbot response to the conversation history
        fin0lyzer_conversation_history.append({"user_input_SA": user_input_fin0lyzer, "chatbot_response": response})
        
    return response
##########################Creation of Stock Analysis Calc.##############################

DF = None
def process_user_input(user_input_fin0lyzer):
    Word = user_input_fin0lyzer.upper()
    WordWithCom = Word + "COM" 
    #Data = Listing_Data[Listing_Data["Initial Letter"] == Word[0]]
    Data = Listing_Data
    Data = Data.reset_index()
    Data.drop("index", axis=1)
    Index = [i for i, token in enumerate(Data["Tokenized_Text"]) if Word in token or WordWithCom in token]
    
    if len(Index) == 0:
        response = "The Company Looking for is NOT Listed in NASDAQ Exchange."
    else:   
        if len(Index) >1:
            Index = Index[0]
        else:
            Index = str(Index)
            Index = int(Index[1:-1])
        Symbol = Data["symbol"][Index]
        DF = API_FuncCompanyData(symbol=Symbol, api_key="your own key")
        
        data = FucForCalcOfPlotsAndCalc(DF)
        generate_plotCAGR(data)
        generate_plotDivYield(data)
        generate_plotPERatio(data)
        generate_plotGPM(data)
        generate_plotNIP(data)
        generate_plotEBIT(data)
        generate_plotEBIDTA(data)
        generate_plotICR(data)
        
        Dict_Data = {}
        Dict_Data["Compound Annual Growth Rate (%)"] = pd.DataFrame(np.where(data["Compound Annual Growth Rate (%)"] > 0,"Yes","No")).value_counts()
        Dict_Data["P/E Ratio"] = pd.DataFrame(np.where(data["P/E Ratio"].between(10,25),"Yes","No")).value_counts()
        Dict_Data["Dividend Yielded (%)"] = pd.DataFrame(np.where(data["Dividend Yielded (%)"].between(1,6),"Yes","No")).value_counts()
        Dict_Data["Gross Profit Margin(%)"] = pd.DataFrame(np.where(data["Gross Profit Margin(%)"]>20,"Yes","No")).value_counts()
        Dict_Data["Net Income Margin (%)"] = pd.DataFrame(np.where(data["Net Income Margin (%)"]>20,"Yes","No")).value_counts()
        Dict_Data["EBIT Margin(%)"] = pd.DataFrame(np.where(data["EBIT Margin(%)"]>15,"Yes","No")).value_counts()
        Dict_Data["EBIDTA Margin (%)"] = pd.DataFrame(np.where(data["EBIDTA Margin (%)"]>15,"Yes","No")).value_counts()
        Dict_Data["Interest Coverage Margin Ratio"] = pd.DataFrame(np.where(data["Interest Coverage Margin Ratio"]>3,"Yes","No")).value_counts()

        #Checking For Number of True and False in each category
        Names_Of_List = list(Dict_Data.keys())
        ListOfTF = []
        for name in Names_Of_List:
            if Dict_Data[name].get("Yes") != None and Dict_Data[name].get("No") != None:
                ListOfTF.append({"Stock Parameter":name,"True_Data":Dict_Data[name].get("Yes"),"False_Data":Dict_Data[name].get("No")})
            
            elif Dict_Data[name].get("Yes") != None:
                ListOfTF.append({"Stock Parameter":name,"True_Data":Dict_Data[name].get("Yes"),"False_Data":0})
            else:
                ListOfTF.append({"Stock Parameter":name,"True_Data":0,"False_Data":Dict_Data[name].get("No")})
        
        FinalDataFrameForWhichStockToChoose = pd.DataFrame(ListOfTF)
    
        #return FinalDataFrameForWhichStockToChoose.to_string()
        #Returning with is stock investable or not
        FinalDataFrameForWhichStockToChoose["Is_Stock_Investable"] = ""
        FinalDataFrameForWhichStockToChoose["Is_Stock_Investable"] = np.where(FinalDataFrameForWhichStockToChoose["True_Data"] > FinalDataFrameForWhichStockToChoose["False_Data"],"Yes","No")
        
        Value_Count_Check = FinalDataFrameForWhichStockToChoose["Is_Stock_Investable"].value_counts()
        
        yes_count = Value_Count_Check.get("Yes", 0)
        no_count = Value_Count_Check.get("No", 0)
        
        if yes_count > no_count:
            response = f"Out of 8 parameters, {yes_count} meet the eligibility, identifying this as a good stock to invest in."
        elif yes_count < no_count:
            response = f"Out of 8 parameters, {no_count} do not meet the eligibility, identifying this as not a good stock to invest in."
        else:
            response = f"Out of 8 parameters, {no_count} meet the eligibility, indicating partial eligibility and suggesting this as a high-risk, low-return stock to invest in."
        
    
    return response

#Function Creation to access the data 
def FucForCalcOfPlotsAndCalc(DF):
# #Laoding the data for each calculation  
    Data_2 = pd.DataFrame(DF[0]["Monthly Adjusted Time Series"])
    Data_2 = Data_2.transpose()
    Data_2 = Data_2.reset_index()

    Adjusted_Data = Data_2.rename({"index" : "timestamp","1. open" : "open","2. high" : "high","3. low" : "low","4. close" : "close","5. adjusted close" : "adjusted close","6. volume" : "volume","7. dividend amount" : "dividend amount"},axis =1)
    Adjusted_Data["open"] = Adjusted_Data["open"].astype("float")
    Adjusted_Data["high"] = Adjusted_Data["high"].astype("float")
    Adjusted_Data["low"] = Adjusted_Data["low"].astype("float")
    Adjusted_Data["close"] = Adjusted_Data["close"].astype("float")
    Adjusted_Data["adjusted close"] = Adjusted_Data["adjusted close"].astype("float")
    #Adjusted_Data["volume"] = Adjusted_Data["volume"].astype("float64")
    Adjusted_Data["dividend amount"] = Adjusted_Data["dividend amount"].astype("float")
    
    #Loading the Income Data 
    IncomeInfo_Df = pd.DataFrame(DF[2]["annualReports"])
    IncomeInfo_Df
    
    #Earning Per Share data
    
    EPS_ForCompany = pd.DataFrame(DF[1]["quarterlyEarnings"])
    #Using Earning Per Share by mapping with our Adjusted_Data 
    #EPS_ForCompany = pd.read_excel("C:/Users/Vidhut Sharma/Downloads/Earnings_companies/Earnings/ibm.xlsx")
    
    EPS_ForCompany = EPS_ForCompany[["fiscalDateEnding","reportedEPS","estimatedEPS","surprise","surprisePercentage"]]
    EPS_ForCompany["fiscalDateEnding"] = pd.to_datetime(EPS_ForCompany["fiscalDateEnding"])
    EPS_ForCompany["Year"] = EPS_ForCompany["fiscalDateEnding"].dt.year
    EPS_ForCompany = EPS_ForCompany[["Year","reportedEPS","estimatedEPS"]]
    # 
    EPS_ForCompany["reportedEPS"] = EPS_ForCompany["reportedEPS"].astype("float")
    EPS_ForCompany["estimatedEPS"] = EPS_ForCompany["estimatedEPS"].replace('None', np.nan)
    EPS_ForCompany["estimatedEPS"] = EPS_ForCompany["estimatedEPS"].astype("float")
    # 
    # Df = pd.DataFrame(Adjusted_Data["open"])
    # Df["close"] = Adjusted_Data["close"]
    # 
    # #Calculating the average open high, open low,adjusted close,dividend amount
    # #Extracting unique years from the data 
    Adjusted_Data["timestamp"] = pd.to_datetime(Adjusted_Data["timestamp"],dayfirst=True)
    Adjusted_Data["Year"] = Adjusted_Data["timestamp"].dt.year
    CheckForYearHave12Month = [year for year in Adjusted_Data["Year"].unique() if len(Adjusted_Data[Adjusted_Data["Year"] == year]) ==12]
    #Subsetting the data only for 10 years
    CheckForYearHave12Month = CheckForYearHave12Month[0:11]
    # 
    # #Creating calculation for Annual calculations to showcase the important ratios
    def CalculateImpFinRatio(DataForCompany,EPS_Data,YearsData):
        #Required Variables For Saving Data
        DataFrameForYear = {}
        DataFrameForQuaterDividend = {}
        ListofQuaterWise = []
        #Filtering the data according to the date
        Year_Data = DataForCompany[DataForCompany["Year"] == YearsData]
        EarningPerShare = EPS_Data[EPS_Data["Year"] == YearsData]
        
        #Filtered data is averaged out open high, open low,close ,adjusted close
        ColName = ["open","high","low","close","adjusted close"]
        
        DataFrameForYear["Year"] = YearsData
    
        for name in ColName: 
            DataFrameForYear[name] = round(sum(Year_Data[name])/len(Year_Data[name]),3)
        
        #Calculation of dividend will be done quaterly wise and then divided by 4 which is the number of quaters in 1 year
        for i in range(0,len(Year_Data),3):
            DataFrameForQuaterDividend[str(i)] = round(sum(Year_Data["dividend amount"][i:i+3]) / len(Year_Data["dividend amount"][i:i+3]),3)
            ListofQuaterWise.append(DataFrameForQuaterDividend[str(i)])
        
        DataFrameDividend = pd.DataFrame(DataFrameForQuaterDividend,index = [0])
        DataFrameDividend["Average Dividend Yielded"] = sum(ListofQuaterWise)/4
        
        DataFrameDividend.rename(columns = {"0": "Dividends in Quater 4","3": "Dividends in Quater 3","6": "Dividends in Quater 2","9": "Dividends in Quater 1"},inplace = True)
        DataFrameDividend = pd.DataFrame(DataFrameDividend["Average Dividend Yielded"])
        DataFrameDividend["Reported Earning Per Share"] = sum(EarningPerShare["reportedEPS"])/4
        #DataFrameDividend["Estimated Earning Per Share"] = sum(EarningPerShare["estimatedEPS"])/4
        DataFrameForOHCAC = pd.DataFrame(DataFrameForYear,index = [0])
    
        return pd.concat([DataFrameForOHCAC,DataFrameDividend],axis =1)
    # 
    ListOfFinCalc = []
    for year in CheckForYearHave12Month:
        ListOfFinCalc.append(CalculateImpFinRatio(DataForCompany = Adjusted_Data,EPS_Data = EPS_ForCompany,YearsData = year))
    # 
    # #Collated list of the Finacial Terms which we will require to showcase    
    FinalListForFinCalcForCompanies = pd.concat(ListOfFinCalc)
    FinalListForFinCalcForCompanies
    
    FinalListForFinCalcForCompanies["Shifted RPS"] = 0
    FinalListForFinCalcForCompanies["Shifted RPS"] = [0] + list(FinalListForFinCalcForCompanies["Reported Earning Per Share"][0:len(FinalListForFinCalcForCompanies)-1])
    FinalListForFinCalcForCompanies = FinalListForFinCalcForCompanies.reset_index()
    FinalListForFinCalcForCompanies.drop("index",axis=1,inplace = True)
    FinalListForFinCalcForCompanies
    # 
    # #Calculating the growth rate for the company
    FinalListForFinCalcForCompanies["Yearly Growth Rate"] = 0
    
    GrowthRateList = []
    GrowthRateList.append(0)
    for i in range(1,len(FinalListForFinCalcForCompanies)):
        Calc = round(((FinalListForFinCalcForCompanies["Reported Earning Per Share"][i] - FinalListForFinCalcForCompanies["Shifted RPS"][i]) / FinalListForFinCalcForCompanies["Shifted RPS"][i])*100,2)
        GrowthRateList.append(Calc)
        
    FinalListForFinCalcForCompanies["Yearly Growth Rate"] = GrowthRateList
    
    # #Check for how many number of years for Compounded Annual Growth Rate
    def CARGCal(Data,NumberOfYears):
        AnnualDict = {}
        StartYear = Data[Data["Year"] == Data["Year"].iloc[0]]["Reported Earning Per Share"].iloc[0]
        YearDiff = Data["Year"][0] - NumberOfYears
        EndYear = Data[Data["Year"] == YearDiff]["Reported Earning Per Share"].iloc[0]
        CAGR = round(((StartYear / EndYear) ** (1/NumberOfYears))-1,4)
        AnnualDict["Number of Years of Average"] = NumberOfYears
        AnnualDict["Compound Annual Growth Rate (%)"] = CAGR*100
        return pd.DataFrame(AnnualDict,index = [0])
    # 
    NumYearList = [1,3,5,7,10]
    GrowthRateList = []
    for i in NumYearList:
        GrowthRateList.append(CARGCal(Data = FinalListForFinCalcForCompanies,NumberOfYears = i))
    FinalCAGR = pd.concat(GrowthRateList)
    
    IncomeInfo_Df = IncomeInfo_Df.iloc[0:11]
    IncomeInfo_Df
    # 
    FinalListForFinCalcForCompanies["Net Income"] = IncomeInfo_Df["netIncome"]
    FinalListForFinCalcForCompanies["Total Revenue"] = IncomeInfo_Df["totalRevenue"]
    FinalListForFinCalcForCompanies["Gross Profit"] = IncomeInfo_Df["grossProfit"]
    FinalListForFinCalcForCompanies["EBIT"] = IncomeInfo_Df["ebit"]
    FinalListForFinCalcForCompanies["EBITDA"] = IncomeInfo_Df["ebitda"]
    FinalListForFinCalcForCompanies["Income Tax Expense"] = IncomeInfo_Df["incomeTaxExpense"]
    FinalListForFinCalcForCompanies["Interest Expense"] = IncomeInfo_Df["interestExpense"]
    
    def ImpRatioCalc(Data,NumberOfYears):
        
        #Final Dict With All Ratio and Percentages
        ImpRatioDict = {}
        
        #Important Ratio and Percentage List
        PE_Ratio = []
        DividendyYield_Ratio = []
        GrossMargin_List = []
        NetProfitMargin_List = []
        EBIT_Margin = []
        EBIDTA_Margin = []
        InterestCoverageRation = []
        
        for i in range(0,NumberOfYears):
            PE_Ratio.append(Data["adjusted close"][i] / Data["Reported Earning Per Share"][i])
            DividendyYield_Ratio.append((Data["Average Dividend Yielded"][i] / Data["adjusted close"][i])*100)
            GrossMargin_List.append((int(Data["Gross Profit"][i]) / int(Data["Total Revenue"][i]))*100)
            NetProfitMargin_List.append((int(Data["Net Income"][i]) / int(Data["Total Revenue"][i]))*100)
            EBIT_Margin.append((int(Data["EBIT"][i]) / int(Data["Total Revenue"][i]))*100)
            EBIDTA_Margin.append((int(Data["EBITDA"][i]) / int(Data["Total Revenue"][i]))*100)
            InterestCoverageRation.append(int(Data["EBIT"][i]) / int(Data["Interest Expense"][i]))
            
        ImpRatioDict["Number of Years of Average"] = NumberOfYears
        ImpRatioDict["P/E Ratio"] = round(sum(PE_Ratio) / NumberOfYears,3)
        ImpRatioDict["Dividend Yielded (%)"] = round(sum(DividendyYield_Ratio) / NumberOfYears,3)
        ImpRatioDict["Gross Profit Margin(%)"] = round(sum(GrossMargin_List) / NumberOfYears,3)
        ImpRatioDict["Net Income Margin (%)"] = round(sum(NetProfitMargin_List) / NumberOfYears,3)
        ImpRatioDict["EBIT Margin(%)"] = round(sum(EBIT_Margin) / NumberOfYears,3)
        ImpRatioDict["EBIDTA Margin (%)"] = round(sum(EBIDTA_Margin) / NumberOfYears,3)
        ImpRatioDict["Interest Coverage Margin Ratio"] = round(sum(InterestCoverageRation) / NumberOfYears,3)
        
        return pd.DataFrame(ImpRatioDict,index = [0])
     
    NumYearList = [1,3,5,7,10]
    ImpRatioListList = []
    
    for i in NumYearList:
        ImpRatioListList.append(ImpRatioCalc(Data = FinalListForFinCalcForCompanies,NumberOfYears = i))
    
    
    FinalFinRatioCalc = pd.concat(ImpRatioListList)
    
    FinalImpAverage_Ratios = FinalCAGR.merge(FinalFinRatioCalc,on = "Number of Years of Average")
    
    return FinalImpAverage_Ratios

#Labels For X-Axis
x_tick_values = ["2023", "2020 to 2023 [3 Years]", "2018 to 2023 [5 Years]", "2016 to 2023 [7 Years]", "2013 to 2023 [10 Years]"]

#Size for each plot
Size = (13.7, 6)

if DF !=None:
    data = FucForCalcOfPlotsAndCalc(DF)
 
#CAGR
def generate_plotCAGR(data):
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize= Size)
    cagr_values = data["Compound Annual Growth Rate (%)"]
    # Generate your Matplotlib plot here
    plt.plot(x_tick_values, cagr_values, marker='o', linestyle='-', color='#4CAF50')   
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Percentages (%)', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Compound Annual Growth Rate Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], cagr_values[i], f'({cagr_values[i]})', fontsize=10, color='#333333', ha='left', va='top')
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    # Adjust layout to center the plot horizontally
    #plt.text(2.1, max(cagr_values) + 3, '*CAGR: It is a measure of the annual growth rate of an investment over a specified period of time.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.8'))
    #plt.text(0.5, -0.1, 'CARG is ....', fontsize=12, fontweight='bold', color='#333333', ha='center', va='center', transform=plt.gca().transAxes)
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/CAGR.png', bbox_inches='tight')
    gc.collect()

#Dividends Yielded    
def generate_plotDivYield(data):
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    div_values = data["Dividend Yielded (%)"]
    plt.plot(x_tick_values, div_values, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Percentages (%)', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Dividends Yielded Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], div_values[i], f'({div_values[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(div_values) + + 0.02, '*Div.Yield: Company annual payout to shareholders from earnings as return on investment.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.8'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/Dividend_Yielded.png', bbox_inches='tight')
    # Clear memory
    gc.collect()

#PE Ratio   
def generate_plotPERatio(data):
    
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    pevalue = data["P/E Ratio"]
    plt.plot(x_tick_values, pevalue, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Ratio', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Profit-to-Earning Ratio Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], pevalue[i], f'({pevalue[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(pevalue) + 4, '*P/E: This ratio compares a company stock price to its earnings per share (EPS), showing its profitability per share', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.8'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/P.E Ratio.png', bbox_inches='tight')
    # Clear memory
    gc.collect()

#Gross Profit Margin
def generate_plotGPM(data):
    
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    gpmvalue = data["Gross Profit Margin(%)"]
    plt.plot(x_tick_values, gpmvalue, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Margin (%)', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Gross Profit Margin Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], gpmvalue[i], f'({gpmvalue[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(gpmvalue) + 1, '*Gross Margin: This typically refers to the total profit earned from sales after deducting the cost of goods sold.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.8'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/GPM.png', bbox_inches='tight')
    # Clear memory
    gc.collect()

#Net Income Margin
def generate_plotNIP(data):
    
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    nipvalue = data["Net Income Margin (%)"]
    plt.plot(x_tick_values, nipvalue, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Margin (%)', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Net Income Margin Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], nipvalue[i], f'({nipvalue[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(nipvalue) + 1, '*Net Income: This margin depicts the income generated after expenses and taxes removal.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.8'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/NetIncomeMargin.png', bbox_inches='tight')
    # Clear memory
    gc.collect()

#EBIT Margin
def generate_plotEBIT(data):
    
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    ebitvalue = data["EBIT Margin(%)"]
    plt.plot(x_tick_values, ebitvalue, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Margin (%)', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Earning Before Interest and Taxes Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], ebitvalue[i], f'({ebitvalue[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(ebitvalue) + 1.4, '*EBIT: Operational profit before interest and taxes.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.6'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/EBIT_Margin.png', bbox_inches='tight')
    # Clear memory
    gc.collect()

#EBIDTA Margin
def generate_plotEBIDTA(data):
    
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    ebidtavalue = data["EBIDTA Margin (%)"]
    plt.plot(x_tick_values, ebidtavalue, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Margin (%)', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Earning Before Interest,Taxes,Depreciation and Amortization Over Time', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], ebidtavalue[i], f'({ebidtavalue[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(ebidtavalue) + 1.5, '*EBITDA : This measures the companys profitability before accounting for certain expenses like interest, taxes, and depreciation.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.6'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/EBIDTA_Margin.png', bbox_inches='tight')
    # Clear memory
    gc.collect()
    
#Interest Coverage Ratio
def generate_plotICR(data):
    
    # Clear previous plot contents
    plt.clf()
    # Increase figure size
    plt.figure(figsize=Size)
    # Generate your Matplotlib plot here
    icrvalue = data["Interest Coverage Margin Ratio"]
    plt.plot(x_tick_values, icrvalue, marker='o', linestyle='-', color='#4CAF50')
    plt.xlabel('Number of Years of Average', fontsize=12, fontweight='bold', color='#333333')
    plt.ylabel('Ratio', fontsize=12, fontweight='bold', color='#333333')
    plt.title('Interest Coverage Ratio', fontsize=14, fontweight='bold', color='#333333')
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.5)
    # Add data labels
    for i in range(len(x_tick_values)):
        plt.text(x_tick_values[i], icrvalue[i], f'({icrvalue[i]})', fontsize=10, color='#333333', ha='left', va='top') 
    # Add legend
    plt.legend(loc='upper right', fontsize=10)
    # Set background color
    plt.gca().set_facecolor('#F5F5F5')
    
    #plt.text(2.1, max(icrvalue) + 2, '*Interest Coverage : This ratio indicates a companys ability to pay interest expenses with its operating income.', fontsize=12, ha='center', bbox=dict(facecolor='#4CAF50', edgecolor='black', boxstyle='round,pad=0.6'))
    # Adjust layout to center the plot horizontally
    plt.subplots_adjust(left=0.1, right=0.9,top = 0.9)
    # Save the plot
    plt.savefig('static/InterestCoverageRatio.png', bbox_inches='tight')
    # Clear memory
    gc.collect()

@app.route('/plot_image')
def plot_image():
    #user_input = request.form['user_input']
    plot_type = request.args.get('type')
    if DF == None:
        data = 0
    elif DF != None:
        data = FucForCalcOfPlotsAndCalc(DF)
    #user_input = request.form['user_input']
        if plot_type == 'A':
            # Check if the plot A image already exists and remove it if so
            if os.path.exists('static/CAGR.png'):
                os.remove('static/CAGR.png')
            generate_plotCAGR(data)
            file_path = os.path.join(app.root_path, 'static', 'CAGR.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
          
            return send_from_directory(os.path.join(app.root_path, 'static'), 'CAGR.png', version_number=file_hash)
        elif plot_type == 'B':
            # Check if the plot B image already exists and remove it if so
            if os.path.exists('static/Dividend_Yielded.png'):
                os.remove('static/Dividend_Yielded.png')
            generate_plotDivYield(data)
            file_path = os.path.join(app.root_path, 'static', 'Dividend_Yielded.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return send_from_directory(os.path.join(app.root_path, 'static'), 'Dividend_Yielded.png', version_number=file_hash)
        
        elif plot_type == 'C':
            if os.path.exists('static/P.E Ratio.png'):
                os.remove('static/P.E Ratio.png')
            generate_plotPERatio(data)
            file_path = os.path.join(app.root_path, 'static', 'P.E Ratio.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return send_from_directory(os.path.join(app.root_path, 'static'), 'P.E Ratio.png', version_number=file_hash)
        elif plot_type == 'D':
            if os.path.exists('static/GPM.png'):
                os.remove('static/GPM.png')
            generate_plotGPM(data)
            file_path = os.path.join(app.root_path, 'static', 'GPM.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            return send_from_directory(os.path.join(app.root_path, 'static'), 'GPM.png', version_number=file_hash)
        elif plot_type == 'E':
            if os.path.exists('static/NetIncomeMargin.png'):
                os.remove('static/NetIncomeMargin.png')
            generate_plotNIP(data)
            file_path = os.path.join(app.root_path, 'static', 'NetIncomeMargin.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return send_from_directory(os.path.join(app.root_path, 'static'), 'NetIncomeMargin.png', version_number=file_hash)
        elif plot_type == 'F':
            if os.path.exists('static/EBIT_Margin.png'):
                os.remove('static/EBIT_Margin.png')
            generate_plotEBIT(data)
            file_path = os.path.join(app.root_path, 'static', 'EBIT_Margin.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return send_from_directory(os.path.join(app.root_path, 'static'), 'EBIT_Margin.png', version_number=file_hash)
        elif plot_type == 'G':
            if os.path.exists('static/EBIDTA_Margin.png'):
                os.remove('static/EBIDTA_Margin.png')
            generate_plotEBIDTA(data)
            file_path = os.path.join(app.root_path, 'static', 'EBIDTA_Margin.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return send_from_directory(os.path.join(app.root_path, 'static'), 'EBIDTA_Margin.png', version_number=file_hash)
        elif plot_type == 'H':
            if os.path.exists('static/InterestCoverageRatio.png'):
                os.remove('static/InterestCoverageRatio.png')
            generate_plotICR(data)
            file_path = os.path.join(app.root_path, 'static', 'InterestCoverageRatio.png')
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return send_from_directory(os.path.join(app.root_path, 'static'), 'InterestCoverageRatio.png', version_number=file_hash)
    
    else:
        return jsonify(message='Plot type not found'), 400

@app.route('/')
def index():
    title = "FinOclik"
    front_text = "Finance on finger clicks"
    about_text = "We as a company wants to establishment financial indpendency and literacy to the users, assist them to gain profit and cross over hurdles of unstability of finance."
    contact_text =" P.O. Loyalist College, Toronto"
    FinOguider = "FinOguider is here to help you with general queries regarding finance whether it is about retirement, investment, terminologies and many more."
    FinOlyzer = "FinOlyzer is here to provide you  stock analytics of top NASDAQ comapnies in tabular and graphical representation, further providing you clarity for investing."  
    
    
    return render_template('index.html', company_title = title, front_text = front_text , about_text = about_text, contact_text = contact_text, FinOguider = FinOguider, FinOlyzer =FinOlyzer)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    chatbot_response = None

    if request.method == 'POST':
        user_input = request.form['user_input']
        chatbot_response = get_chatbot_response(user_input)

    return render_template('chatbot.html', chatbot_response=chatbot_response, conversation_history=conversation_history)


@app.route('/FinOlyzer', methods=['GET', 'POST'])
def FinOlyzer():
    chatbot_response = load_fin0lyzer_conversation_history()
    return render_template('FinOlyzer_test.html', chatbot_response=chatbot_response)

@app.route('/get_fin0lyzer_chatbot_response', methods=['POST'])
def get_fin0lyzer_chatbot():
    
    try:
        if request.method == 'POST':
            user_input = request.json.get('user_input_SA')  # Get user input from JSON request data
            chatbot_response = get_fin0lyzer_chatbot_response(user_input)
            
            # Update conversation history
            #fin0lyzer_conversation_history.append({"user_input_SA": user_input, "chatbot_response": chatbot_response})
            
            # Save conversation history to file
            save_fin0lyzer_conversation_history()
            
            return jsonify({"chatbot_response": chatbot_response})
    except Exception as e:
        return repr(e)


if __name__ == "__main__":
    app.run(debug=True)
    