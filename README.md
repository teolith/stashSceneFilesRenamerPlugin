# SceneFilesRenamer

This is a Stash plugin by Teo Lith, which enables users to rename scene file(s) to a customizable template
by updating the scene's metadata in the [Edit] tab.

It is loosely based on the RenameFile plugin by David Maisonave (aka Axter) albeit a complete rewrite.

I started off looking for a rename plugin which suited my needs.  
In the end I was not happy with the choices made by other rename plugin authors.  
This caused me to write my own.  
Note this wouldn't have been possible without the work of the other rename plugin authors.  

## Rename Template
The central feature of this rename plugin is the configurable *Rename Template*.  
Here you can define the scene filename in terms of scene properties.

Assume *Rename Template* is set to `[$(studio)] $(title)`  
It contains two *Property Placeholders*, namely `$(studio)` and `$(title)`.  
Updating a scene with studio `"Wow"` and title `"Oh my goodness"` will cause the associated `mp4` file to rename to `"[Wow] Oh my goodness.mp4"`.  

### Syntax
The syntax for the *Rename Template* is any text interspersed with *Property Placeholders*.  
A simple *Property Placeholder* looks like `$(property)`.

A *Property Placeholder* can optionally contain one or more *Format Specifiers*.  
*Format Specifiers* enable manipulating the property it's value before it is put into the new filename.  
A *Property Placeholder* with one *Format Specifier* without options looks like `$(property:format)`.  
A *Property Placeholder* with two *Format Specifiers* with options looks like `$(property:format1(options1):format2(options2))`.  

### Supported properties
- studio
  - no format specifiers
- title
  - no format specifiers
- performers
  - filter:  
    e.g. `filter(female)` formats Susan, John and Lisa as `Susan, Lisa`  
    available filters are `all`, `female`, `male`, `!female`, and `!male`
  - seperator:   
    e.g. `seperator(, )` formats Susan, John and Lisa as `Susan, John, Lisa`
- date
  - *strftime pattern*:  
    e.g. `%Y-%m-%d` formats January 12, 2026 as `2026-01-12`
- width
  - no format specifiers
- height
  - no format specifiers

### Example
A more elaborate example of a *Rename Template*:  
`[$(studio)] $(title) - $(performers:filter(!male):separator(, )) ($(date:%Y-%m-%d)) [$(height)p]`

## Tasks
Next to the rename functionality on scene update, this plugin supplies two Tasks.

* Run (rename all scene files) for last updated Studio.  
  This task allows to update all scene files for a given studio by first updating a studio and then running this task.
* Dry run (rename all scene files) for last updated Studio.  
  Like *Run* but without actually renaming.
