"""
Display logic for presenting the menu.
"""

from __future__ import absolute_import

import curses

import nyx.curses
import nyx.popups
import nyx.controller
import nyx.menu.item
import nyx.menu.actions

from nyx.curses import RED, WHITE, NORMAL, BOLD, UNDERLINE, HIGHLIGHT


class MenuCursor:
  """
  Tracks selection and key handling in the menu.
  """

  def __init__(self, initial_selection):
    self._selection = initial_selection
    self._is_done = False

  def is_done(self):
    """
    Provides true if a selection has indicated that we should close the menu.
    False otherwise.
    """

    return self._is_done

  def get_selection(self):
    """
    Provides the currently selected menu item.
    """

    return self._selection

  def handle_key(self, key):
    is_selection_submenu = isinstance(self._selection, nyx.menu.item.Submenu)
    selection_hierarchy = self._selection.get_hierarchy()

    if key.is_selection():
      if is_selection_submenu:
        if not self._selection.is_empty():
          self._selection = self._selection.get_children()[0]
      else:
        self._is_done = self._selection.select()
    elif key.match('up'):
      self._selection = self._selection.prev()
    elif key.match('down'):
      self._selection = self._selection.next()
    elif key.match('left'):
      if len(selection_hierarchy) <= 3:
        # shift to the previous main submenu

        prev_submenu = selection_hierarchy[1].prev()
        self._selection = prev_submenu.get_children()[0]
      else:
        # go up a submenu level

        self._selection = self._selection.get_parent()
    elif key.match('right'):
      if is_selection_submenu:
        # open submenu (same as making a selection)

        if not self._selection.is_empty():
          self._selection = self._selection.get_children()[0]
      else:
        # shift to the next main submenu

        next_submenu = selection_hierarchy[1].next()
        self._selection = next_submenu.get_children()[0]
    elif key.match('esc', 'm'):
      self._is_done = True


def show_menu():
  with nyx.popups.popup_window(1, below_static = False) as (popup, width, height):
    if popup:
      control = nyx.controller.get_controller()

      # generates the menu and uses the initial selection of the first item in
      # the file menu

      menu = nyx.menu.actions.make_menu()
      cursor = MenuCursor(menu.get_children()[0].get_children()[0])

      while not cursor.is_done():
        # sets the background color

        popup.win.clear()
        popup.win.bkgd(' ', nyx.curses.curses_attr(RED, HIGHLIGHT))
        selection_hierarchy = cursor.get_selection().get_hierarchy()

        # provide a message saying how to close the menu

        control.set_msg('Press m or esc to close the menu.', BOLD, True)

        # renders the menu bar, noting where the open submenu is positioned

        draw_left, selection_left = 0, 0

        for top_level_item in menu.get_children():
          if top_level_item == selection_hierarchy[1]:
            attr = UNDERLINE
            selection_left = draw_left
          else:
            attr = NORMAL

          draw_label = ' %s ' % top_level_item.get_label()[1]
          popup.addstr(0, draw_left, draw_label, BOLD, attr)
          popup.vline(0, draw_left + len(draw_label), 1)

          draw_left += len(draw_label) + 1

        # recursively shows opened submenus

        _draw_submenu(cursor, 1, 1, selection_left)

        popup.win.refresh()

        curses.cbreak()
        cursor.handle_key(control.key_input())

        # redraws the rest of the interface if we're rendering on it again

        if not cursor.is_done():
          control.redraw()

  control.set_msg()


def _draw_submenu(cursor, level, top, left):
  selection_hierarchy = cursor.get_selection().get_hierarchy()

  # checks if there's nothing to display

  if len(selection_hierarchy) < level + 2:
    return

  # fetches the submenu and selection we're displaying

  submenu = selection_hierarchy[level]
  selection = selection_hierarchy[level + 1]

  # gets the size of the prefix, middle, and suffix columns

  all_label_sets = [entry.get_label() for entry in submenu.get_children()]
  prefix_col_size = max([len(entry[0]) for entry in all_label_sets])
  middle_col_size = max([len(entry[1]) for entry in all_label_sets])
  suffix_col_size = max([len(entry[2]) for entry in all_label_sets])

  # formatted string so we can display aligned menu entries

  label_format = ' %%-%is%%-%is%%-%is ' % (prefix_col_size, middle_col_size, suffix_col_size)
  menu_width = len(label_format % ('', '', ''))

  with nyx.popups.popup_window(len(submenu.get_children()), menu_width, top, left, below_static = False) as (popup, _, _):
    if not popup:
      return

    # sets the background color

    popup.win.bkgd(' ', nyx.curses.curses_attr(RED, HIGHLIGHT))

    draw_top, selection_top = 0, 0

    for menu_item in submenu.get_children():
      if menu_item == selection:
        draw_format = (WHITE, BOLD)
        selection_top = draw_top
      else:
        draw_format = (NORMAL,)

      popup.addstr(draw_top, 0, label_format % menu_item.get_label(), *draw_format)
      draw_top += 1

    popup.win.refresh()

    # shows the next submenu

    _draw_submenu(cursor, level + 1, top + selection_top, left + menu_width)
