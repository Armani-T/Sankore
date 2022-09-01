# Sankore

> What if you had a personal GoodReads?

Sankore is a small personal project that I built to keep track of my reading habits. It keeps track of the books I have and which ones I'm reading now. Since it works offline, I prefer it to GoodReads. All the data is stored in a JSON file so syncing it's easily accessible anywhere and makes syncing a breeze.

## Installation

First, ensure that you have `python3` on your system and that the version `3.9.0` or above. If it isn't, you can download/update it either from `apt-get` or from <https://python.org/downloads/>. Now that that's out of the way, we can get the app and its' dependencies. You can do this by running:

```bash
$ git clone https://github.com/Armani-T/Sankore
$ cd Sankore
$ pip install -r requirements.txt
```

## Usage

First, navigate to wherever you clones the repo to. Then, you `cd` into the `Sankore/` folder and from there you can run the app using `python3`. Here is how the process would look like:

```bash
$ cd cloned/repo/location  # replace this with the real path to the repo.
$ cd Sankore  # note the capital letter.
$ python3 sankore
```

The app should now start running. On start up, it should look like this:

![Home page](assets/home.png)

![New book page](assets/new-book.png)

![New library page](assets/new-book.png)

![Update page part 1/2](assets/update-1.png)

![Update page part 2/2](assets/update-2.png)

## Contributing Guide

Please use GitHub issues for any bug reports or feature requests.

1. Create your branch by forking `develop`.
2. Fix the bug/Create the feature.
3. Push your changes.
4. Open a pull request.

## Meta

- Name: **Armani Tallam**
- E-Mail: armanitallam@gmail.com
- GitHub: <https://www.github.com/Armani-T>

This project is licensed under the **MIT License**. Please see the [license file](LICENSE) for more information.