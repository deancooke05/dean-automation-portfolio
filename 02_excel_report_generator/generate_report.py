from pathlib import Path
import pandas as pd
inp=Path('sample_data/sample_sales.csv')
out=Path('outputs/Weekly_Sales_Report.xlsx')
df=pd.read_csv(inp)
summary=pd.DataFrame({'Metric':['Total Revenue','Orders','Average Order'],'Value':[df['revenue'].sum(),len(df),round(df['revenue'].mean(),2)]})
out.parent.mkdir(exist_ok=True)
with pd.ExcelWriter(out,engine='openpyxl') as w:
    df.to_excel(w,index=False,sheet_name='Raw Data')
    summary.to_excel(w,index=False,sheet_name='Summary')
print('Created',out)
