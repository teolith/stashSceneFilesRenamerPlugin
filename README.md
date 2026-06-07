# SceneFilesRenamer

This is a Stash plugin by Teolith, which enables renaming scene files to a customizable template
by updating the scene's metadata in the [Edit] tab.

It is loosely based on the RenameFile plugin by David Maisonave (aka Axter) albeit a complete rewrite.

I started off looking for a rename plugin which suited my needs.  
In the end I was not happy with the choices made by other rename plugin authors.  
This caused me to write my own plugin (wired with my choices).  
Note this wouldn't have been possible without the work of the other Rename plugin authors.  

## Content
- [Disclaimer](#Disclaimer)
- [Rename Template](#Rename-Template)
  - [Syntax](#Syntax)
  - [Supported properties](#Supported-properties)
  - [Example](#Example)
- [Dry run](#Dry-run)
- [Logging](#Logging)
  - [Debug tracing](#Debug-tracing)
- [Tasks](#Tasks)

## Disclaimer
I only ever tested this plugin on my own setup and have gotten the results I expected.  
I am aware that there are probably a lot of corner cases I haven't seen yet and as such weren't able to address yet.  
Please bare this in mind when it screws up on your system.

## Rename Template
The central feature of this rename plugin is the configurable *Rename Template* 
(Settings > Plugins > Plugins > SceneFilesRenamer > Rename Template).  
Here you can define the scene filename in terms of scene properties.

Assume *Rename Template* is set to `[$(studio)] $(title)`.  
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
    e.g. `filter(female)` formats Susan, John and Lisa as `Susan, Lisa` (assuming Susan and Lisa are male and John is not).  
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

## Dry run
The *Dry run* settingin the plugin's configuration enables running without actually renaming files (Settings > Plugings > Plugins > SceneFilesRenamer > Dry run).  
Although this doesn't catch renaming issues like illegal characters, readonly files or name clashes, it will enable to preview what the plugin would rename the found files to. 

## Logging
This plugin logs to Stash's own log (Settings > Logs).  
To enable focussing on log entries from this plugin, it also logs to its own logfile in the plugin's directory:  
`<plugin-dir>/sceneFilesRenamer.log`.

### Debug tracing
It is also possible to enable *Debug tracing* to get more verbose logging in the plugin's configuration (Settings > Plugings > Plugins > SceneFilesRenamer > Debug Tracing).

## Tasks
Next to the rename functionality on scene update, this plugin supplies two Tasks.

* Run (rename all scene files) for last updated Studio.  
  This task allows to update all scene files for a given studio by first updating a studio and then running this task.
* Dry run (rename all scene files) for last updated Studio.  
  Like *Run* but without actually renaming.
