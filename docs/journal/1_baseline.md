# Week 1 Technical Documnetation

## Technical Goals
Build a baseline agent architecture from scratch. Understand how each component works so we have full control over agent implementation.

## Technical Uncertainty

### Troubleshooting Ruby Bundler
I didn't have Ruby installed, so I looked up how to do that. I realized Bundler had to be installed too. I had trouble installing that via gem; it kept hanging the terminal (I'm using WSL within VS Code). I ended up installing it at user level using `gem install bundler --user-install`. Now when running the 00_config script, I received error

> Could not find dotenv-3.2.0 in locally installed gems

and it told me to run `bundle install` to install missing gems. When running `bundle install`, it gave me a permission error. I tried running it with `sudo` but then the `bundle` command is not found, since it's installed only for the user. I used Claude for some help and it recommended installing gems into vendor/bundle using `bundle config set --local path 'vendor/bundle'`. I did that and then ran `bundle install` again and it was successful!

I added a couple of lines to my `.gitignore` to exclude the Ruby `vendor/bundle` directories/files.

### Troubleshooting Ruby example.rb
This brought me up to the point where Andrew was in the Config Ruby video at about 24:30. However, I still got an error even after renaming `settings.yml` to `settings.yaml`. I used Claude to assist in troubleshooting. It had me provide specific bits of the Ruby files, and a directory listing of the `.boukensha` directory. It found that `settings.yaml` was 0 bytes! I had pasted the settings in but forgot to save it. After fixing that, I was able to get the proper output when running `00_config`.

## Technical Hypotheses
I expect we will have a better Player Agent than we did when using the models in preweek.

## Technical Observations
- I spent more time than I imagined I would on simply getting Ruby and Bundle set up.
- Claude/Sonnet did very well writing the plan to port the Ruby code over to Python, including asking the relevant questions.

## Technical Conclusions


## Key Takeaway
