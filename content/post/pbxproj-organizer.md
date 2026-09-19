+++
date = "2017-06-02T12:24:00-04:00"
draft = false
image = "pbxproj-organizer/hero.png"
title = "Stay Organized + Save Time Using pbxproj_organizer.py"

description = "Recently I've been trying to keep my commit history clean and organized with better branch management and more frequent commits, but one file kept taking up an inordinate amount of time. Here's how I fixed that."

+++

Recently I've been trying to keep my commit history clean and organized with better branch management and more frequent commits, but one file kept taking up an inordinate amount of time. Can you guess which one?

<div class="figure" style="border-style: none none solid none;">
	<img src="/blog/images/pbxproj-organizer/sourcetree.png">
</div>
<span class="caption"><b>Above</b> Even a small change to your Xcode project can seem to cause a cascade of changes to your <code>project.pbxproj</code> file inside of your <code>.xcodeproj</code> file.</span>

Yup, it's `project.pbxproj`, a hidden file within your project's `.xcodeproj` file. This file is created, used, and managed by Xcode to keep track of all the files, folders, and frameworks in your project, including the way your files are organized in your Project navigator within Xcode. It also keeps track of your project's settings and metadata.

In theory, this is a file you shouldn't have to touch, and for the most part, you don't have to touch it all. However, some issues arise when you're working on multiple branches and attempting to merge things back together. For example, let's say that you have two branches that you're working on, and within each branch, you've separately imported the same class (`HelloWorld.h`/`.m`). What happens when you try to merge these two branches together?

<div class="figure" style="border-style: none none solid none;">
	<img src="/blog/images/pbxproj-organizer/merge_conflict.png">
</div>
<span class="caption"><b>Above</b> Merge conflicts arise because identical files imported on different branches are assigned unique UUIDs by Xcode. Failing to use a consistent UUID for each imported file can cause issues opening your Xcode project.</span>

Ideally, git (or whatever version control you're using) should recognize that the two separately imported references are the same file. However, because Xcode generates a unique UUID for each imported reference, the two `HelloWorld` files will have different UUIDs. Since git is agnostic to what you're committing, it won't recognize that these two imports are actually for the same file, so you'll have to resolve this conflict manually during merging.

If you're only working with a few files, these merge conficts are pretty easy to resolve, especially if you're using a visual editor like [SourceTree](https://www.sourcetreeapp.com). However, as your project comes to encompass more and more files, frameworks, and imports, the time it takes to manage `pbxproj.xcodeproj` seems to grow exponentially.

There are two additionally vexing behaviors of Xcode which make manually sorting your `project.pbxproj` file even more time consuming. The first is that Xcode will sort the files and references in your `project.pbxproj` file alphabetically based on their UUIDs. This sorting isn't completely random, as Xcode generates UUIDs in alphabetically increasing order (so that newly created or imported files have higher UUIDs than older files), but it is obnoxious. The second behavior is that Xcode sorts `pbxproj.xcodeproj` each time you build. 😑

## Solving Sorting Through Scripting!

Thankfully, computers are the ideal tool for performing tedious repetitive tasks quickly and automatically. As such, I've written a Python script called **[KMHXcodeTools](https://github.com/kenmhaggerty/KMHXcodeTools)** that will organize your `project.pbxproj` file each time you build based on how your files and folders are sorted in your Project navigator in Xcode.

To use this script, simply download or fork from [GitHub](https://github.com/kenmhaggerty/KMHXcodeTools), copy the `pbxproj_organizer.py` file into your Xcode project's directory so that it is a sibling to your `.xcodeproj` file, and add the following Run Script under Build Phases in Xcode:

<div class="figure">
	<img src="/blog/images/pbxproj-organizer/pbxproj_run_script.png">
</div>
<span class="caption"><b>Above</b> The run script above will execute each time you build your Xcode project. The text contained acts as if entered into your computer's Terminal from within your project's directory.</span>

And that's it! Now, instead of having to manually reorganize your `project.pbxproj` file just to see if any files have indeed been added or removed, the script will do it automatically, saving hours of time each time you commit.

## How It Works; or, Regex To The Rescue!

This script uses [regular expressions](https://regexone.com) to search for textual patterns in `project.pbxproj` and parse the file accordingly. For us, this means determining the order by which we want to sort our files and then sorting all sections where these files are referenced in order to maintain consistent sorting across branches.

For simplicity's sake, I've put all of my code in a single file (so that you only have to import one file), but if you take a look inside of `pbxproj_organizer.py`, you'll see a bunch of functions for actually performing the sorting followed by the script that calls those functions.

There's a lot of code inside of `pbxproj_organizer.py`, so I won't go over what all of it does line-by-line, but here's a high-level overview of what it does:

1. **Open `project.pbxproj`**  
Pretty straightforward, but key. If you have multiple `.xcodeproj` files in your directory, the script will sort each one's `project.pbxproj` file.
2. **Determine Order Using PBXGroup Section**  
In addition to determining our sort order via the parent-child relationships in the PBXGroup section, this steps also searches the PBXBuildFile section for additional identifiers for certain files (e.g., `.m`, `.xcassets`, and `.storyboard` files), as some sections of `project.pbxproj` use this identifier rather than the value for `fileRef`.
3. **Update Sections Using Extracted Order**  
The six main sections of `project.pbxproj` our code touches are PBXBuildFile, PBXFileReference, PBXFrameworksBuildPhase, PBXGroup, PBXResourcesBuildPhase, and PBXSourcesBuildPhase.
4. **Save Changes To `project.pbxproj`**  
Also straightforward but key.

What that means for you is that instead of seeing this:

<div class="figure" style="border-style: none;">
	<img src="/blog/images/pbxproj-organizer/before.png">
</div>

you'll now see this:

<div class="figure" style="border-style: none;">
	<img src="/blog/images/pbxproj-organizer/after.png">
</div>

which I think we can all agree is a whole lot better! 😅

## Questions? Suggestions?

As always, please let me know what you think, and feel free to contribute, either by [forking my repo](https://help.github.com/articles/fork-a-repo/) on GitHub and [submitting a pull request](https://help.github.com/articles/creating-a-pull-request/) for your submissions or else just [emailing me](mailto:kenmhaggerty@gmail.com?Subject=%5Bpbxproj_organizer.py%5D+Reader+Response) directly.
