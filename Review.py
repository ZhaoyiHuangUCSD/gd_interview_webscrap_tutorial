#这个是initalize object， 这个就比较集成化
class Review:
	def __init__(self, date, role, gotOffer, experience, difficulty, length, details, questions):
		self.date = date
		self.role = role
		self.gotOffer = gotOffer
		self.experience = experience
		self.difficulty = difficulty
		self.length = length
		self.details = details
		self.questions = questions
	#enddef