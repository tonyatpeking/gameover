// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {


	// Utility function to check if the cursor is on a whitespace or empty character
	function isCursorOnWhitespaceOrEmpty(): boolean {
		const editor = vscode.window.activeTextEditor;
		if (editor) {
			const position = editor.selection.active;
			const document = editor.document;
			const character = document.getText(new vscode.Range(position, position.translate(0, 1)));
			return character === '' || /\s/.test(character);
		}
		return false;
	}
	function getCursorPosition(): vscode.Position | null {
		const editor = vscode.window.activeTextEditor;
		if (editor) {
			return editor.selection.active;
		}
		return null;
	}
	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "gameover" is now active!');
	vscode.commands.executeCommand('setContext', 'gameover.moveMode', true);

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	//#region commands
	let disposable = vscode.commands.registerCommand('gameover.helloWorld', () => {
		// The code you place here will be executed every time your command is executed
		// Display a message box to the user
		let message = 'Hello World from gameover! Modified';
		vscode.window.showInformationMessage(message);
	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.moveLeft', async () => {
		// vscode.commands.executeCommand('vscode.executeWorkspaceSymbolProvider', 's').then(
		// 	function (symbols) {
		// 		console.log(symbols);
		// 	});
		const editor = vscode.window.activeTextEditor;
		const document = editor!.document;
		const cursorPos = editor!.selection.active;
		document.lineAt(cursorPos).range.end.character;

		await vscode.commands.executeCommand('cursorWordAccessibilityLeft');
		await vscode.commands.executeCommand('cursorWordAccessibilityLeft');
		let position = getCursorPosition();
		while (isCursorOnWhitespaceOrEmpty()) {
			await vscode.commands.executeCommand('cursorWordAccessibilityLeft');
			const newPosition = getCursorPosition();
			if (position === newPosition) {
				// break out if cursor is not moving
				break;
			}
			position = newPosition;
		}
		await vscode.commands.executeCommand('cursorWordRightSelect');
	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.moveRight', async () => {
		await vscode.commands.executeCommand('cursorWordAccessibilityRight');
		let position = getCursorPosition();
		while (isCursorOnWhitespaceOrEmpty()) {
			await vscode.commands.executeCommand('cursorWordAccessibilityRight');
			const newPosition = getCursorPosition();
			if (position === newPosition) {
				// break out if cursor is not moving
				break;
			}
			position = newPosition;
		}
		await vscode.commands.executeCommand('cursorWordRightSelect');

	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.moveUp', () => {
		const editor = vscode.window.activeTextEditor;
		if (editor) {
			const position = editor.selection.active;
			const document = editor.document;
			const character = document.getText(new vscode.Range(position, position.translate(0, 1)));
			const isWhitespaceOrEmpty = character === '' || /\s/.test(character);
			vscode.window.showInformationMessage(`Character ${character} is Whitespace or empty: ${isWhitespaceOrEmpty}`);
			console.log(isWhitespaceOrEmpty);
		}
	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.moveDown', () => {
		vscode.commands.executeCommand('cursorWordStartLeftSelect');
		console.log('not implemented');
	});
	context.subscriptions.push(disposable);


	//#endregion
}

// This method is called when your extension is deactivated
export function deactivate() { }
