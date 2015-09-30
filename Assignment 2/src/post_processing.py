import os


class Page:
	def __init__(self):
		self.mapping = {} #string to id.
		self.content_files = [] #Names on my pc
		self.original_names = [] #Names on internet

	def read_mapping(self):
		f = open("Mapping.txt")
		for line in f:
			mp = line.split("\t")
			self.mapping[mp[1]] = mp[0] #Translation.
			self.content_files.append(mp[0]) #Names on my pc
			self.original_names.append(mp[1]) #Names on internet
		f.close()

	def process(self):
		for filename in self.content_files:
			f = open(filename,"r") #Do i need filemode? is it two way?
			all_data = f.read()
			for ref in self.original_names:
				all_data = self.mapping[ref].join(all_data.split(ref))
			f.close()
			f = open(filename, "r")
			f.write(all_data)
			f.close()

if __name__=="__main__":
	webpage = Page()
	webpage.read_mapping()
	webpage.process()