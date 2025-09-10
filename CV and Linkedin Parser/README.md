Name: GEORGE TONMOY
Email: georgetonmoy07@gmail.com
Mobile Number: 8801828113
Skills: ['System', 'Python', 'Nltk', 'Schedules', 'Analysis', 'International', 'Mining', 'Mysql', 'Spacy', 'Mobile', 'Css', 'Engineering', 'Facebook', 'Safety', 'Pytorch', 'Numpy', 'Seaborn', 'English', 'Matplotlib', 'Hardware', 'Programming', 'Rest', 'Api', 'Communication', 'Analyze', 'Html', 'Postgresql', 'Oracle', 'Metrics', 'Data analysis', 'Math', 'Pandas', 'C', 'Ai', 'Database', 'Github', 'Sql', 'Research', 'Java', 'Engagement', 'P', 'Js', 'Cloud', 'Operations', 'C++', 'Computer science', 'Django', 'Analytics', 'Android', 'Javascript', 'Website']
College Name: None
Degree: None
Designation: None
Company Names: None
No Of Pages: 2
Total Experience: 0.42

import nltk
nltk.download('stopwords')

from pyresparser import ResumeParser
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
data = ResumeParser("George_Tonmoy_Roy_AI_2025.pdf").get_extracted_data()
print("Name:", data["name"])
print("Email:", data["email"])
print("Mobile Number:", data["mobile_number"])
print("Skills:", data["skills"])
print("College Name:", data["college_name"])
print("Degree:", data["degree"])
print("Designation:", data["designation"])
print("Company Names:", data["company_names"])
print("No Of Pages:", data["no_of_pages"])
print("Total Experience:", data["total_experience"])
