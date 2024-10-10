import wx


class NumericValidator(wx.Validator):
    def __init__(self):
        super(NumericValidator, self).__init__()
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        """Required method for validators."""
        return NumericValidator()

    def Validate(self, win):
        """Validates the input when the focus changes or the dialog is submitted."""
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()

        # Allow empty field (optional)
        if text == "":
            return True
        
        # Check if the input is a valid number (int or float)
        try:
            float(text)
            return True
        except ValueError:
            wx.MessageBox("Please enter a valid number.", "Invalid Input")
            textCtrl.SetFocus()
            return False

    def TransferToWindow(self):
        """Not used here, but required for validator subclass."""
        return True

    def TransferFromWindow(self):
        """Not used here, but required for validator subclass."""
        return True

    def OnChar(self, event):
        """Filters keypresses to allow only digits, a single period, or backspace."""
        key = event.GetKeyCode()

        # Allow ASCII control characters (backspace, delete, arrow keys)
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key == wx.WXK_BACK:
            event.Skip()
            return

        # Allow digits (0-9) or period ('.')
        if chr(key).isdigit() or chr(key) == '.':
            textCtrl = self.GetWindow()
            text = textCtrl.GetValue()
            
            # Ensure only one period is allowed
            if chr(key) == '.' and '.' in text:
                return  # Discard the second period
            event.Skip()  # Accept the keypress
        else:
            # Discard the keypress (invalid input)
            return
