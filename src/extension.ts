// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

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

	disposable = vscode.commands.registerCommand('gameover.i', () => {
		vscode.commands.executeCommand('vscode.executeWorkspaceSymbolProvider', 's').then(
			function (symbols) {
				console.log(symbols);
			});

	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.j', () => {
		vscode.commands.executeCommand('cursorWordEndLeftSelect');
		console.log('j');
	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.k', () => {
		vscode.commands.executeCommand('cursorWordStartLeftSelect');
		console.log('k');
	});
	context.subscriptions.push(disposable);

	disposable = vscode.commands.registerCommand('gameover.l', () => {
		vscode.commands.executeCommand('cursorWordLeftSelect');
		console.log('l');
	});
	context.subscriptions.push(disposable);
	//#endregion
}

// This method is called when your extension is deactivated
export function deactivate() { }
