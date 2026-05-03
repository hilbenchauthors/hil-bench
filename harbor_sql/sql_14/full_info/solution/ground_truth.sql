SELECT County, COUNT(InstructionType) 
FROM schools 
WHERE (County = 'San Diego' OR County = 'Santa Barbara') 
  AND InstructionType = 'T' 
  AND DOC = '52'
GROUP BY County 
ORDER BY COUNT(InstructionType) DESC 