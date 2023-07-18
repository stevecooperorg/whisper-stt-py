setup:
	brew bundle
	cd src && pip3 install -r requirements.txt

run:
	cd src && python3 transcribe.py \
	   --input "/directory/with/your/mp4files" \
	   --output "/final/answer/goes/in/here" \
	   --splits "/intermediate/files/go/here"